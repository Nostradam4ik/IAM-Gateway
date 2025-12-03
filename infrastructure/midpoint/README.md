## midPoint resources (local templates)

This folder contains template resource definitions for midPoint and a short
explanation how to use them.

- `resources/hr-csv.xml` : template CSV resource. Edit the `<file>` path to
  point to a CSV file available to the midPoint container (e.g. `/opt/midpoint/var/post-initial-objects/hr_sample.csv`).
- `resources/ldap-resource.xml` : template LDAP resource configured for ApacheDS.

Quick usage notes:

1. Copy the sample CSV into the running midPoint container so the resource can access it:

```bash
docker compose -f infrastructure/docker/docker-compose.midpoint.yml exec midpoint mkdir -p /opt/midpoint/var/post-initial-objects
docker cp datasets/hr_sample.csv midpoint-core:/opt/midpoint/var/post-initial-objects/hr_sample.csv
```

2. In the midPoint UI: `Resources` → `Import` → upload `infrastructure/midpoint/resources/hr-csv.xml` and `ldap-resource.xml` (edit them first if needed).

3. After import, create/run the CSV Import Task (Tasks → Run task) to ingest users.

4. If you need an automated initial object import, place XMLs under `/opt/midpoint/var/post-initial-objects/` in the container before the app starts.
