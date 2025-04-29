#!/usr/bin/env python3

import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
import os

# Paths
NIFI_HOME = "/opt/nifi"
USERS_XML_PATH = Path(NIFI_HOME) / "conf/users.xml"
AUTH_XML_PATH = Path(NIFI_HOME) / "conf/authorizations.xml"

# Environment variable for number of replicas
replica_count = int(os.environ.get("NIFI_REPLICA_COUNT", "1"))

# Helper Functions
def gen_uuid(prefix, value):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{prefix}:{value}"))

def indent(elem, level=0):
    """Add indentation to an ElementTree for pretty printing."""
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            indent(e, level + 1)
        if not e.tail or not e.tail.strip():
            e.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i

def ensure_minimal_users_xml():
    if not USERS_XML_PATH.exists() or USERS_XML_PATH.stat().st_size == 0:
        tenants = ET.Element('tenants')
        ET.SubElement(tenants, 'groups')
        ET.SubElement(tenants, 'users')
        tree = ET.ElementTree(tenants)
        tree.write(USERS_XML_PATH, encoding="utf-8", xml_declaration=True)
        print("Created minimal users.xml")

def ensure_minimal_authorizations_xml():
    if not AUTH_XML_PATH.exists() or AUTH_XML_PATH.stat().st_size == 0:
        authorizations = ET.Element('authorizations')
        ET.SubElement(authorizations, 'policies')
        tree = ET.ElementTree(authorizations)
        tree.write(AUTH_XML_PATH, encoding="utf-8", xml_declaration=True)
        print("Created minimal authorizations.xml")

def ensure_user(tree, root, identity):
    user_id = gen_uuid("user", identity)

    users_element = root.find('users')
    if users_element is None:
        raise Exception("No <users> section found in users.xml")

    for u in users_element.findall("user"):
        identifier = u.attrib.get("identifier")
        if identifier == user_id:
            return False

    user = ET.Element("user", attrib={"identifier": user_id, "identity": identity})
    users_element.append(user)
    print(f"Added user {identity}")
    return True

def ensure_policy(tree, root, resource, action, identity):
    user_id = gen_uuid("user", identity)

    policies_element = root.find('policies')
    if policies_element is None:
        raise Exception("No <policies> section found in authorizations.xml")

    # Map action: "read" -> "R", "write" -> "W"
    action_map = {
        "read": "R",
        "write": "W"
    }
    action_attr = action_map.get(action.lower(), action)

    # Try to find an existing policy for resource + action
    for policy in policies_element.findall("policy"):
        if (policy.attrib.get("resource") == resource and
            policy.attrib.get("action") == action_attr):
            # Check if this user is already in the policy
            for user in policy.findall("user"):
                if user.attrib.get("identifier") == user_id:
                    return False  # User already present
            # Add user to existing policy
            ET.SubElement(policy, "user", attrib={"identifier": user_id})
            print(f"Added user {identity} to existing policy on {resource} ({action_attr})")
            return True

    # No existing policy: create a new one
    policy_id = gen_uuid("policy", f"{resource}:{action}:{identity}")
    policy = ET.Element("policy", attrib={
        "identifier": policy_id,
        "resource": resource,
        "action": action_attr
    })
    ET.SubElement(policy, "user", attrib={"identifier": user_id})
    policies_element.append(policy)
    print(f"Created new policy {action_attr} on {resource} for {identity}")
    return True

def main():
    ensure_minimal_users_xml()
    ensure_minimal_authorizations_xml()

    users_tree = ET.parse(USERS_XML_PATH)
    users_root = users_tree.getroot()
    auth_tree = ET.parse(AUTH_XML_PATH)
    auth_root = auth_tree.getroot()

    changed = False

    # 1. Monitoring user
    monitoring_id = "CN=monitoring"
    changed |= ensure_user(users_tree, users_root, monitoring_id)
    for res in ["/controller", "/flow", "/system", "/counters", "/provenance"]:
        changed |= ensure_policy(auth_tree, auth_root, res, "read", monitoring_id)

    # 2. NiFi node users
    print(f"Configuring {replica_count} NiFi nodes")
    for i in range(replica_count):
        node_identity = f"CN=nifi-node{i}"
        changed |= ensure_user(users_tree, users_root, node_identity)
        for res in ["/site-to-site", "/proxy"]:
            for action in ["read", "write"]:
                changed |= ensure_policy(auth_tree, auth_root, res, action, node_identity)

    if changed:
        indent(users_root)
        indent(auth_root)
        users_tree.write(USERS_XML_PATH, encoding="utf-8", xml_declaration=True)
        auth_tree.write(AUTH_XML_PATH, encoding="utf-8", xml_declaration=True)
        print("Updated and formatted NiFi authorization files.")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    main()
