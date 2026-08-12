// Minimal markdown renderer - covers what the curriculum's instructions
// actually use (headers, bold/italic, inline code, links, lists,
// paragraphs). Not a general-purpose parser; a full one would be a CDN
// dependency (marked.js, etc.) rather than reinvented here.
function renderMarkdown(source) {
  const escaped = source
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  const lines = escaped.split("\n");
  const htmlParts = [];
  let listBuffer = [];

  function flushList() {
    if (listBuffer.length) {
      htmlParts.push(`<ul>${listBuffer.join("")}</ul>`);
      listBuffer = [];
    }
  }

  function inline(text) {
    return text
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`(.+?)`/g, "<code>$1</code>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushList();
      continue;
    }

    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) {
      flushList();
      const level = heading[1].length;
      htmlParts.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      continue;
    }

    const listItem = line.match(/^[-*]\s+(.*)$/);
    if (listItem) {
      listBuffer.push(`<li>${inline(listItem[1])}</li>`);
      continue;
    }

    flushList();
    htmlParts.push(`<p>${inline(line)}</p>`);
  }
  flushList();

  return htmlParts.join("\n");
}
