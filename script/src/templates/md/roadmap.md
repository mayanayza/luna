---
layout: page
title: Roadmap
permalink: /roadmap/
---

## In Progress

{% if in_progress %}
| Project | Description |
|---------|-------------|
{% for project in in_progress %}
{%- if project.name in public_repos -%}
| <a href='{{ github }}/{{ project.name }}' target='_blank'>{{ project.display_name }}</a> | {{ project.description | default('') }} |
{%- else -%}
| {{ project.display_name }} | {{ project.description | default('') }} |
{%- endif -%}
{% endfor %}
{% else %}
Nothing currently in progress
{% endif %}

## Backlog

{% if backlog %}
| Project | Description |
|---------|-------------|
{% for project in backlog %}
| {{ project.display_name }} | {{ project.description | default('') }} |
{% endfor %}
{% else %}
Nothing currently in backlog
{% endif %}