---
layout: page
title: Links
permalink: /links/
hide_header: true
---

<div class="links-container" style="display: flex; flex-direction: column; align-items: center; gap: 1rem; width: 100%;">
<h2>Featured Work</h2>
{% for post in featured_posts %}
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('{{ post.url }}', '_blank')">
  {% if post.image %}
  <div class="button-image">
    <img src="{{ post.image }}" alt="{{ post.name }}">
  </div>
  {% endif %}
    {{ post.title }}
</div>
{% endfor %}
<br />
<h2>Links</h2>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('{{ website }}/', '_blank')">Portfolio</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('{{ website }}/roadmap', '_blank')">Roadmap</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('{{ github }}', '_blank')">Github</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://dev.to/mayanayza', '_blank')">Dev.to</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://cara.app/mayanayza/', '_blank')">Cara</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://hackaday.io/mayanayza', '_blank')">Hackaday.io</div>
<div class="button button--primary" style="width: 100%; display: flex; justify-content: center; text-align: center;" onclick="window.open('https://www.hackster.io/mayanayza', '_blank')">Hackster.io</div>
</div>