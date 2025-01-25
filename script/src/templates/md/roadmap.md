---
layout: page
title: Roadmap
permalink: /roadmap/
---

## In Progress
{% if in_progress %}
| Project | Description |
|---------|-------------|
{%- for project in in_progress %}
{%- if project.github %}
| <a href='{{ project.github }}' target='_blank'>{{ project.display_name }}</a> | {{ project.description }} |
{%- else %}
| {{ project.display_name }} | {{ project.description | default('') }} |
{%- endif %}
{%- endfor -%}
{% else %}
Nothing currently in progress
{% endif %}

## Backlog
{% if backlog %}
| Project | Description |
|---------|-------------|
{%- for project in backlog %}
| {{ project.display_name }} | {{ project.description }} |
{%- endfor -%}
{% else %}
Nothing currently in backlog
{% endif %}