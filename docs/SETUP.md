# Set up Microsoft 365 Copilot with MongoDB Atlas

These demos combine current operational records in Atlas with collaboration context in Teams
and policies in OneDrive. For example, [Leafy Tech](../demos/leafy-tech/README.md) checks a hospital
laptop quote against warehouse stock, nurses' requirements, customer terms and rebate rules.
The same pattern can support procurement, field service and customer support.

Copilot calls the managed Atlas MCP server using the signed-in user's delegated authorization.
The Python scripts use a separate database credential to load and verify sample data. A successful
Python query does not establish that Copilot can access the same data. See the
[architecture overview](../SETUP_ORIENTATION.md) for the request path and permission model.

## Accounts, access and costs

| Requirement | What to arrange |
|---|---|
| Microsoft work or school tenant | A Microsoft Entra account, an eligible base subscription and an assigned Microsoft 365 Copilot license for the licensed capabilities used here |
| Microsoft 365 services | Teams and work OneDrive/SharePoint, with access to the sample posts and documents |
| Microsoft administrator | Someone authorized to manage connector availability, user access and rollout |
| Atlas organization and project | An individual Atlas identity with read access to the demo project; an Organization Owner to enable AI client access |
| Atlas sandbox | A disposable cluster and database, supported networking and billing; the reference demos used M10 |
| Python | Python 3 and the dependencies in `requirements.txt`; the demos were developed with Python 3.13 |

Microsoft requires a qualifying base license and a Copilot license for licensed Copilot
capabilities. Free chat access or a personal subscription does not establish those entitlements.
Check the exact plans and included services with your tenant administrator using
[Microsoft's requirements](https://learn.microsoft.com/en-us/copilot/plan/microsoft-copilot-requirements)
and [license options](https://learn.microsoft.com/en-us/copilot/plan/copilot-license-options).
Inspect assigned licenses in **Users → Active users → selected user → Licenses and apps**.

Budget for Microsoft subscriptions, Atlas compute runtime, storage and applicable network
transfer. Semantic search also uses embedding capacity for indexed text and query text. Check
current [embedding billing](https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/billing/)
and your Atlas billing settings. An M10 reference is not a claim about the cheapest supported
configuration. Throughput quotas and request limits describe allowed rates; they are neither
consumed tokens nor billed usage. One chat prompt can cause multiple tool calls.

The managed integration needs no application server, separately deployed model, custom agent
or Microsoft Foundry resource. Keep the existing indexes and data between demo runs to avoid
unnecessary loading and embedding work.

## 1. Prepare the local source

Clone or download the repository and open a terminal at its root. Keep the scripts, JSON
fixtures and document files together.

On macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Use `.venv\Scripts\python.exe` in place of `.venv/bin/python` in subsequent commands on
Windows. These Windows examples have not been executed in the reference environment.

## 2. Configure Atlas and load sample data

1. Create or select a dedicated sandbox project and cluster. Use generic names such as
   **copilot-demo** and **demo-cluster**. Confirm the selected tier and region support the demo's
   features before provisioning.
2. Create a database user for Python, scoped to the demo database. Loading requires writes;
   index creation also requires the applicable index-management privileges. Use separate,
   narrower credentials when only reading data.
3. Allow the terminal's actual egress IP or approved network range under **Network Access**.
   A private network deployment needs a reachable route from the terminal. This connection is
   separate from Copilot's delegated authorization.
4. Open **Connect → Drivers** and put the connection string in the ignored `.env` file with
   your editor. URL-encode special characters in the password. Do not paste credentials into
   Copilot, screenshots or issues.

```dotenv
MONGODB_URI="mongodb+srv://<database-user>:<encoded-password>@<cluster-host>/"
MONGODB_DB_TECH=leafy_tech
```

For Leafy Tech, load the committed fixture into an empty sandbox:

```bash
.venv/bin/python demos/leafy-tech/scripts/load_atlas.py
.venv/bin/python demos/leafy-tech/scripts/demo_queries.py --check
```

The loader creates 332 products, 300 customers, 3,101 orders and 61 quotes, plus ordinary
indexes and the `product_semantic` vector index. It refuses existing demo data. Use
`--replace-demo-data` only to deliberately replace disposable data; it retains the products
collection and its search index. `--no-vector` is for local script testing and leaves semantic
search unconfigured. See each [demo's README](../README.md) for its own loading requirements.

Leafy Tech uses Automated Embedding on `products.description` with `voyage-4`. Atlas generates
and stores embeddings rather than requiring application-managed vectors. Dedicated M10+
clusters require storage auto-scaling for this feature. Automated Embedding is documented as
Preview independently of the GA connector; verify supported deployments and feature status in
the [MongoDB documentation](https://www.mongodb.com/docs/vector-search/crud-embeddings/automated-embedding/).

To inspect the index, open the cluster's **Search & Vector Search**, select **leafy_tech →
products**, and check **product_semantic**. Its definition is:

```json
{
  "fields": [
    {"type": "autoEmbed", "modality": "text", "path": "description", "model": "voyage-4"},
    {"type": "filter", "path": "category"},
    {"type": "filter", "path": "status"}
  ]
}
```

Wait for queryability and run the actual query checks. An index badge establishes configuration
status, not that Copilot has executed a vector query.

## 3. Enable the managed connector

In Atlas, an Organization Owner enables AI client access in **Organization Settings → App
Connections**, using **Read** mode. Give each Copilot user's Atlas identity the appropriate
project data-read role. Access follows that identity's roles; a database name in a prompt is
not an authorization boundary. See [Atlas AI client access](https://www.mongodb.com/docs/mcp-server/remote-mcp/manage-ai-client-access/).

In the Microsoft 365 admin center, enable **MongoDB Atlas** under **Copilot → Connectors → Your
connections** and include the intended users in staged rollout. Also check **Agents → Settings
→ Agent and plugin access**, **User access**, and applicable tool policies. Microsoft lists
Global Administrator or Search Administrator for managing federated connector availability;
other AI administration tasks can have different role requirements. Follow the
[connector-management guide](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/manage-federated-connectors).

After policy propagation, sign in as the intended user. In Copilot, open **Add and manage sources
→ Change data sources**, or **Settings → Sources** in older navigation. Select MongoDB Atlas
and complete its browser sign-in. A source can require reconnection after its grant expires.
Do not substitute the Python database password for this interactive authorization.

## 4. Add Teams and OneDrive context

For Leafy Tech, create **Leafy Tech (DEMO) → Willow Bend Refresh** in Teams and publish the five
posts from the [seed sheet](../demos/leafy-tech/teams/TEAMS_MESSAGES.md). “Posting for” names the
fictional speaker; separate actor accounts are unnecessary.

Upload the three [OneDrive documents](../demos/leafy-tech/onedrive/) to a work folder and share
them with the intended users. Allow time for search indexing, then test under those users'
identities. Elapsed time alone is not proof of readiness. The
[fallback channel export](../demos/leafy-tech/fallback/) can demonstrate document retrieval,
but cannot establish retrieval of an actual Teams post.

## 5. Verify both retrieval paths

Run the direct checks and the prompts in the selected demo's walkthrough. The Leafy Tech
[walkthrough](../demos/leafy-tech/DEMO_SCRIPT.md) includes a reversible inventory change and
semantic matching.

| Observation | What it establishes |
|---|---|
| Direct Python checks pass | The script credential reaches the fixture and the checked query results match expectations |
| Copilot returns the specified database's fresh records | The delegated connector can retrieve those records; compare with an independent read |
| A new inventory change appears in a fresh Copilot tool result | Live retrieval of the changed record, rather than a plausible answer from the original fixture |
| A citation opens the intended Teams post or OneDrive document | Retrieval of that source; inspect its body and permissions |
| An inspectable request contains `$vectorSearch` on the intended namespace and index | Actual semantic execution; ranked prose or a separately run Python query alone is insufficient |

If the interface hides the request, record semantic execution as unverified until independent
request evidence is available. Model behavior varies; earlier named-model observations in
the demo scripts are rehearsal results, not availability guarantees.

## Troubleshooting

| Symptom | Check |
|---|---|
| Atlas source is missing | License assignment, tenant policy, connector enablement, user access and staged rollout |
| Source shows Reconnect | Complete Atlas authorization in the intended browser profile and confirm the return to Copilot |
| Python cannot connect | URI encoding, database-user role, DNS and the terminal's network route/allowlist |
| Wrong data appears | Actual project, cluster, database and identity permissions; compare fresh records independently |
| Teams post is absent | Membership, indexing, exact subject and whether Copilot cited an export instead |
| Semantic search fails | Queryable index, correct definition, supported Automated Embedding configuration and exposed `aggregate` tool |

Undo the demo's live change when finished. Revoke unused grants and remove disposable
resources through their owners when no longer needed. Keep credentials and real account
details out of repository contributions.
