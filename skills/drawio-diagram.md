---
name: drawio-diagram
description: Create professional diagrams (flowcharts, architecture, ERD, sequence, mind maps) from concepts and knowledge using drawio MCP. Use when content needs visual representation - triggered by explicit requests or auto-suggested for architectural/process/relationship content.
---

# Drawio Diagram Skill

Generate professional diagrams using the drawio MCP server with real-time browser preview.

## Quick Start

```
1. Start session: mcp__drawio__start_session (opens browser preview)
2. Create diagram: mcp__drawio__display_diagram with natural language or XML
3. Refine: mcp__drawio__edit_diagram for modifications
4. Export: mcp__drawio__export_diagram to save .drawio file
```

## MCP Tools Reference

| Tool | Purpose | Parameters |
|------|---------|------------|
| `mcp__drawio__start_session` | Open browser with real-time preview | None |
| `mcp__drawio__display_diagram` | Create new diagram | XML or natural language description |
| `mcp__drawio__edit_diagram` | Modify existing diagram | Edit operations (update/add/delete cells) |
| `mcp__drawio__get_diagram` | Retrieve current diagram XML | None |
| `mcp__drawio__export_diagram` | Save to .drawio file | File path |
| `mcp__drawio__append_diagram` | Handle large/truncated diagrams | Partial diagram data |

## Diagram Types & Triggers

### 1. Flowchart

**Use For**: Process workflows, decision trees, user journeys, step-by-step procedures

**Trigger Keywords**: process, workflow, steps, decision tree, flow

**Example Prompt**:
```
Create a flowchart for user authentication:
1. User enters credentials
2. Validate input format
3. Check database
4. If valid: create session, redirect to dashboard
5. If invalid: show error, allow retry (max 3 times)
6. If locked: show lockout message
```

### 2. Architecture Diagram

**Use For**: System design, component diagrams, infrastructure layouts, microservices

**Trigger Keywords**: architecture, system, components, infrastructure, design

**Example Prompt**:
```
Create a system architecture diagram:
- Frontend: React app on Vercel
- API: FastAPI on AWS Lambda
- Auth: Auth0
- Database: PostgreSQL on RDS
- Cache: Redis on ElastiCache
- Storage: S3 for files
Show connections and data flow between components.
```

### 3. Mind Map

**Use For**: Concept relationships, knowledge hierarchies, brainstorming, topic exploration

**Trigger Keywords**: mind map, concepts, relationships, brainstorming

**Example Prompt**:
```
Create a mind map for "AI Agent Architecture":
- Core: AI Agent
- Branches:
  - Memory: Short-term, Long-term, Episodic
  - Tools: MCP, Function Calling, RAG
  - Planning: ReAct, Chain-of-Thought, Tree-of-Thought
  - Learning: Fine-tuning, RLHF, In-context
```

### 4. Sequence Diagram

**Use For**: API interactions, communication flows, request/response patterns

**Trigger Keywords**: sequence, interactions, API flow, request/response

**Example Prompt**:
```
Create a sequence diagram for OAuth2 login:
Actors: User, Frontend, Auth Server, Resource Server
1. User clicks login
2. Frontend redirects to Auth Server
3. User authenticates
4. Auth Server returns auth code
5. Frontend exchanges code for tokens
6. Frontend requests resource with token
7. Resource Server validates and responds
```

### 5. ERD (Entity Relationship Diagram)

**Use For**: Database schemas, data models, entity relationships

**Trigger Keywords**: ERD, entity, data model, tables, schema, database

**Example Prompt**:
```
Create an ERD for a blog system:
- User (id, email, name, created_at)
- Post (id, user_id, title, content, published_at)
- Comment (id, post_id, user_id, content, created_at)
- Tag (id, name)
- PostTag (post_id, tag_id)
Relationships: User has many Posts, Post has many Comments, Post has many Tags
```

## Generation Workflow

### Step 1: Start Session
```
mcp__drawio__start_session

Result: Browser opens with draw.io editor
- Real-time preview on port 6002-6020 (auto-selected)
- Version history available (clock button, bottom-right)
```

### Step 2: Analyze Content for Diagram Structure
```
From extracted content, identify:
- Key entities/concepts (nodes)
- Relationships/flows (edges)
- Groupings/layers (containers)
- Labels and descriptions
```

### Step 3: Generate Diagram
```
mcp__drawio__display_diagram

Input: Natural language description OR draw.io XML
- Describe the diagram clearly
- Specify layout preference (horizontal/vertical)
- Mention styling needs (colors, shapes)
```

### Step 4: Iterate with User
```
Show preview in browser
Accept refinement requests:
- "Add connection between A and B"
- "Change color of X to blue"
- "Remove the Y component"
- "Reorganize layout vertically"

Use: mcp__drawio__edit_diagram for each modification
```

### Step 5: Export and Save
```
mcp__drawio__export_diagram

File Path: [same folder as related note]/[topic]-diagram-[YYYY-MM-DD].drawio

Examples:
- Zettelkasten/AI-research/MCP-Architecture-diagram-2025-01-02.drawio
- Research/OAuth-Flow-diagram-2025-01-02.drawio
- Threads/Agent-Concepts-diagram-2025-01-02.drawio
```

### Step 6: Link to Notes
```markdown
## Visualization

![[Topic-diagram-2025-01-02.drawio]]

*Diagram: Brief description*
```

## File Naming Convention

```
[topic]-diagram-[YYYY-MM-DD].drawio

Rules:
- Topic: English or local language, use hyphens instead of spaces
- Location: Same folder as related notes
- Date: ISO format (YYYY-MM-DD)

Examples:
- User-Authentication-Flow-diagram-2025-01-02.drawio
- MCP-Server-Architecture-diagram-2025-01-02.drawio
```

## Note Integration Patterns

### Pattern 1: Embed in Existing Note
```markdown
# [Note Title]

## Content
[Note content here...]

## Visualization
![[Topic-diagram-2025-01-02.drawio]]

*Figure: Diagram description*
```

### Pattern 2: Standalone Diagram Note
```markdown
---
id: YYYYMMDDHHmm
type: diagram
tags: [diagram, visualization, topic-tag]
diagram_file: "[[Topic-diagram-2025-01-02.drawio]]"
related_notes: ["[[Related Note 1]]", "[[Related Note 2]]"]
---

# [Diagram Title]

## Overview
[What this diagram represents]

## Diagram
![[Topic-diagram-2025-01-02.drawio]]

## Key Elements
- **Element A**: Description
- **Element B**: Description
- **Connection A→B**: Relationship description

## Related Notes
- [[Related Note 1]] - Connection reason
- [[Related Note 2]] - Connection reason
```

## Best Practices

### 1. One Diagram, One Concept
- Keep diagrams focused on a single idea
- Complex systems → multiple linked diagrams
- Avoid overcrowding

### 2. Consistent Styling
- Use visual hierarchy (size, color, position)
- Group related elements
- Maintain consistent shape meanings

### 3. Clear Labeling
- Label all connections
- Use descriptive node names
- Add legend for complex diagrams

### 4. Meaningful File Names
- Include topic and diagram type
- Use dates for versioning
- Keep names scannable

### 5. Bidirectional Linking
- Diagram references notes
- Notes reference diagram
- Maintain relationship context

## Error Handling

### Browser Preview Not Opening
```
1. Check if port 6002-6020 is available
2. Retry with mcp__drawio__start_session
3. Manual fallback: generate XML for external import
```

### Diagram Generation Fails
```
1. Simplify the description
2. Break into smaller parts
3. Use explicit XML structure
4. Retry with more specific instructions
```

### Export Fails
```
1. Check file path permissions
2. Verify folder exists
3. Use absolute path if needed
4. Manual save from browser UI
```

## Integration with Knowledge Manager

This skill integrates with knowledge-manager at:

1. **Phase 3.5**: Visualization opportunity detection
2. **Phase 4**: Output format option (diagram)
3. **Phase 5F**: Diagram export workflow

Trigger patterns:
- Explicit: "create diagram", "make a flowchart", "visualize this"
- Auto-detect: Process steps, system components, entity relationships
