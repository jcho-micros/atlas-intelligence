# Workflow Engine Design

## Goal

Move product projects through a defined lifecycle using agent tasks and events.

## Concepts

### Product Project

A business object created from an opportunity.

### Agent Task

A unit of work assigned to an agent.

### Agent Event

A permanent record of what happened.

### Workflow Rule

A condition that advances a project or creates new tasks.

## Example

```text
project.created
    → create task: product_designer.generate_brief
    → create task: finance.estimate_margin

finance.margin_approved
    → create task: manufacturing.find_supplier

manufacturing.supplier_found
    → create task: launch.prepare_checklist
```
