function markdownElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderInlineMarkdown(parent, text, resolveWikiLink) {
  // shortcut: links use flat labels, extend the parser if nested Markdown labels are needed.
  const pieces = text.split(/(\[\[[^\]\n]+\]\]|\[[^\]\n]+\]\([^\s)]+\)|\*\*[^*\n]+\*\*|`[^`\n]+`)/g);
  for (const piece of pieces) {
    if (!piece) continue;
    const wiki = piece.match(/^\[\[([^|\]]+)(?:\|([^\]]+))?\]\]$/);
    const link = piece.match(/^\[([^\]]+)\]\(([^\s)]+)\)$/);
    if (wiki || link) {
      const label = wiki ? wiki[2] || wiki[1] : link[1];
      const href = wiki ? resolveWikiLink?.(wiki[1]) : link[2];
      let allowed = false;
      try { allowed = ['https:', 'http:', ...(wiki ? ['obsidian:'] : [])].includes(new URL(href, 'http://localhost').protocol) && Boolean(href); } catch {}
      if (allowed) {
        const anchor = markdownElement('a', '', label);
        anchor.setAttribute('href', href);anchor.setAttribute('target', '_blank');anchor.setAttribute('rel', 'noopener noreferrer');
        parent.append(anchor);
      } else parent.append(document.createTextNode(label));
    } else if (piece.startsWith('**') && piece.endsWith('**')) {
      parent.append(markdownElement('strong', '', piece.slice(2, -2)));
    } else if (piece.startsWith('`') && piece.endsWith('`')) {
      parent.append(markdownElement('code', '', piece.slice(1, -1)));
    } else {
      parent.append(document.createTextNode(piece));
    }
  }
}

function tableCells(line) {
  let value = line.trim();
  if (value.startsWith('|')) value = value.slice(1);
  if (value.endsWith('|')) value = value.slice(0, -1);

  const cells = [];
  let cell = '';
  let escaped = false;
  for (const character of value) {
    if (escaped) {
      cell += character;
      escaped = false;
    } else if (character === '\\') {
      escaped = true;
      cell += character;
    } else if (character === '|') {
      cells.push(cell.trim().replace(/\\\|/g, '|'));
      cell = '';
    } else {
      cell += character;
    }
  }
  cells.push(cell.trim().replace(/\\\|/g, '|'));
  return cells;
}

function tableAlignment(line) {
  const cells = tableCells(line);
  if (!cells.length || !cells.every(cell => /^:?-{3,}:?$/.test(cell))) return null;
  return cells.map(cell => cell.startsWith(':') && cell.endsWith(':') ? 'center' : cell.endsWith(':') ? 'right' : 'left');
}

function appendTable(container, lines, start, resolveWikiLink) {
  const headings = tableCells(lines[start]);
  const alignments = tableAlignment(lines[start + 1]);
  if (!alignments || headings.length !== alignments.length) return 0;

  const wrapper = markdownElement('div', 'markdown-table-wrap');
  const table = markdownElement('table', 'markdown-table');
  const head = markdownElement('thead');
  const headRow = markdownElement('tr');
  headings.forEach((heading, index) => {
    const cell = markdownElement('th');
    cell.setAttribute('data-align', alignments[index]);
    renderInlineMarkdown(cell, heading, resolveWikiLink);
    headRow.append(cell);
  });
  head.append(headRow);

  const body = markdownElement('tbody');
  let cursor = start + 2;
  while (cursor < lines.length && lines[cursor].trim().includes('|')) {
    const values = tableCells(lines[cursor]);
    if (values.length !== headings.length) break;
    const row = markdownElement('tr');
    values.forEach((value, index) => {
      const cell = markdownElement('td');
      cell.setAttribute('data-align', alignments[index]);
      renderInlineMarkdown(cell, value, resolveWikiLink);
      row.append(cell);
    });
    body.append(row);
    cursor += 1;
  }

  table.append(head, body);
  wrapper.append(table);
  container.append(wrapper);
  return cursor - start;
}

function renderMarkdown(body, {headingOffset, resolveWikiLink} = {}) {
  const container = markdownElement('div', 'explanation-body');
  const lines = body.replace(/\r\n?/g, '\n').split('\n');
  let paragraph = [];
  let list = null;
  let listTag = null;

  const flush = () => {
    if (!paragraph.length) return;
    const node = markdownElement('p');
    renderInlineMarkdown(node, paragraph.join(' '), resolveWikiLink);
    container.append(node);
    paragraph = [];
  };
  const resetList = () => { list = null; listTag = null; };

  for (let index = 0; index < lines.length;) {
    const line = lines[index].trim();
    if (!line) {
      flush();
      resetList();
      index += 1;
      continue;
    }

    if (index + 1 < lines.length && line.includes('|')) {
      const headings = tableCells(line);
      const alignments = tableAlignment(lines[index + 1]);
      if (alignments && headings.length === alignments.length) {
        flush();
        resetList();
        index += appendTable(container, lines, index, resolveWikiLink);
        continue;
      }
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flush();
      resetList();
      const node = markdownElement(`h${headingOffset === undefined ? 4 : Math.min(6, heading[1].length + headingOffset)}`);
      renderInlineMarkdown(node, heading[2], resolveWikiLink);
      container.append(node);
      index += 1;
      continue;
    }

    const bullet = line.match(/^[-*]\s+(.+)$/);
    const ordered = line.match(/^\d+[.)]\s+(.+)$/);
    if (bullet || ordered) {
      flush();
      const tag = ordered ? 'ol' : 'ul';
      if (!list || listTag !== tag) {
        list = markdownElement(tag);
        listTag = tag;
        container.append(list);
      }
      const item = markdownElement('li');
      renderInlineMarkdown(item, (bullet || ordered)[1], resolveWikiLink);
      list.append(item);
      index += 1;
      continue;
    }

    resetList();
    paragraph.push(line);
    index += 1;
  }

  flush();
  return container;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {renderMarkdown, tableCells, tableAlignment};
}
