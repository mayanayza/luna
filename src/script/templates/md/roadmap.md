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
{% if project.github %}
| <a href='{{ project.github }}' target='_blank'>{{ project.display_name }}</a> | {{ project.tagline }} |
{% else %}
| {{ project.display_name }} | {{ project.tagline | default('') }} |
{% endif %}
{% endfor %}
{% else %}
Nothing currently in progress
{% endif %}

## Backlog

{% if backlog %}
| Project | Description |
|---------|-------------|
{% for project in backlog %}
| {{ project.display_name }} | {{ project.tagline }} |
{% endfor %}
{% else %}
Nothing currently in backlog
{% endif %}

## Complete

{% if in_progress %}
| Project | Description |
|---------|-------------|
{% for project in complete %}
{% if project.website %}
| <a href='{{ project.website }}' target='_blank'>{{ project.display_name }}</a> | {{ project.tagline }} |
{% else %}
| {{ project.display_name }} | {{ project.tagline | default('') }} |
{% endif %}
{% endfor %}
{% else %}
Nothing completed
{% endif %}
