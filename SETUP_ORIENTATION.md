# How Copilot talks to Atlas

For technical audiences. Takes about three minutes to present.

For accounts, licensing, administrative configuration and validation, use
the [setup guide](docs/SETUP.md). This page is the architecture overview.

## The path of one question

```
You type in Copilot Chat
      |
      v
Microsoft 365 Copilot picks a tool at run time
      |   federated connector: live call, nothing indexed into Microsoft 365
      v
MongoDB MCP server (tools: find, aggregate, count, list-collections...)
      |   short-lived credentials that carry your identity
      v
Atlas cluster: the answer comes from the data as it is right now
```

MCP, the Model Context Protocol, is a standard way for an AI client to discover and call tools.
Teams and OneDrive answers come through Microsoft 365. Atlas answers come through this path.
Copilot combines them in one reply.

## Setup in five steps

**In Atlas**

1. **Allow AI clients.** An Organization Owner opens Organization Settings, then App Connections,
   and sets the access mode to Read. It is off by default for existing organizations, and the
   setting applies to the whole organization.
2. **Give people data access.** Each user needs an Atlas role that reaches the data, such as
   Project Data Access Read Only. Copilot can never do more than that user can do.
3. **Add a vector index if you want meaning search.** With Automated Embedding, the index
   definition names the text field and the model. Atlas does the embedding. You write no
   embedding code and store no vectors in your documents.

**In Microsoft 365**

4. **Turn on the connector.** An administrator with the effective connector-management role opens the Microsoft 365
   admin center, then Copilot, then Connectors. Enable the connector and stage it to a pilot group.
   Microsoft's connector availability guide currently lists Global Administrator or Search Administrator;
   see the setup guide for the role/task distinction and current navigation.
5. **Each user connects once.** In Copilot Chat: the ... menu, Settings, Sources, select the
   source, Connect. The user signs in to Atlas in the browser.

A user sees the connector only if all of these allow it: the agent and plugin access setting,
the connector being enabled, the user access setting, staged rollout, and a Microsoft 365
Copilot license.

## Questions technical people ask

| Question | Answer |
|---|---|
| Is our data indexed in Microsoft 365? | Federated Atlas retrieval does not synchronize data into the Microsoft 365 search index. Requested results are transmitted to Copilot for reasoning. |
| Whose permissions apply? | The signed-in user's. Copilot cannot exceed their Atlas role. |
| Does Copilot see a connection string? | No. Atlas never exposes database connection details or user credentials to the client. |
| Can it write? | In Read mode, write tools are not offered to the client. `aggregate` is still offered, but `$out` and `$merge` fail. |
| Does access expire? | Yes. By default after 7 days of inactivity, or 30 days from the grant. An Organization Owner can shorten this. |
| Can we restrict it to one project? | Not with the organization setting. It applies organization-wide, and access follows each user's roles. |
| Is it audited? | Atlas does not record each tool call. Events that are audited record the user and the AI client. Microsoft says admins can audit connector activity in Purview. |
| What about a database outside Atlas? | The managed MCP server reaches Atlas clusters only. For anything else, run the MCP server yourself. |
| Can we build our own connector? | Yes: a custom federated connector needs an MCP server URL, a description, and Entra SSO, OAuth 2.0 or no authentication. |

## Tips from building these demos

These are historical presenter observations, not guaranteed behavior for every tenant or model.
Validate the actual model and tool calls before relying on a demo.

- Pick a named model in Copilot's model picker. New chats start on Auto, and in our tests Auto
  did not call the connector. Each demo names the models that worked in rehearsal.
- Prompt wording drives tool choice. "Similar in meaning" brought back `$vectorSearch`. "In Teams"
  limited Copilot to Teams.
- A field has to exist for a question to work. "Added today" failed because the catalog had no
  date-added field. "Most recently updated" worked.
- Atlas is live, but Teams is not instant. Atlas changes appear in the next answer. Teams posts
  can take several hours or more to become searchable, so post them at least two days ahead.
- The connector must expose `aggregate`, because `$vectorSearch` runs inside an aggregation.

## Sources

- [Federated connectors overview](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/federated-connectors-overview)
- [Set up custom federated connectors](https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/set-up-custom-federated-connectors)
- [MCP access models for MongoDB Atlas](https://www.mongodb.com/docs/mcp-server/remote-mcp/access-models)
- [Manage AI client access](https://www.mongodb.com/docs/mcp-server/remote-mcp/manage-ai-client-access)
- [Security, governance and auditability](https://www.mongodb.com/docs/mcp-server/remote-mcp/security)
