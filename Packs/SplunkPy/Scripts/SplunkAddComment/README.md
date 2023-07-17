Use this script to add a comment with a tag (the "Comment tag to Splunk" defined in the instance configuration) as an entry in XSOAR, which will then be mirrored as a comment to a Splunk issue. This script should be run within an incident.

## Script Data

---

| **Name** | **Description** |
| --- | --- |
| Script Type | python3 |
| Cortex XSOAR Version | 6.0.0 |

## Inputs

---

| **Argument Name** | **Description** |
| --- | --- |
| comment | comment to be added to the Splunk issue. |
| tags | The comment tag. Use the comment entry tag \(defined in your instance configuration\) to mirror the comment to splunk. |

## Outputs

---
There are no outputs for this script.
