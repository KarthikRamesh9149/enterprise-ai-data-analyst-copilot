# Agent Workflow

State includes question, dataset id, intent, plan, summary, and critic output.

Nodes:
- Intent classifier: maps question to SQL analytics, EDA, modeling, or forecasting.
- Schema inspector: summarizes dataset schema/profile context.
- Planner: records governed execution steps.
- Critic: flags unsupported claims and governance gaps.

The workflow is deterministic for local demos. It persists trace rows so the UI can show node-level execution. SQL execution remains outside autonomous control and requires approval.
