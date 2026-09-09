/* EditorialMarkdown.js
   Neue Zürcher Zeitung (NZZ) - Broadsheet Markdown & Editorial Typography Engine
   Parses raw markdown headings (#, ##, ###), bold (**text**), italics (*text*),
   blockquotes (> text), lists (- / 1.), links, and code into semantic Swiss broadsheet elements.
*/

function EditorialMarkdown(props) {
  const { text, className = '' } = props;
  if (!text) return null;

  // Render inline formatting (bold, italics, code, links, quotes)
  const renderInline = (str) => {
    if (!str) return [];
    const tokens = [];
    let remaining = str;
    let keyIdx = 0;

    // Pattern for bold (**..** or __..__), code (`..`), link ([..](..)), swiss quotes («..»), double quotes (".."), italics (*..* or _.._)
    const regex = /(\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|`[^`]+`|\[[^\]]+\]\([^)]+\)|«[^»]+»|"[^"]{4,}")/;

    while (remaining) {
      const match = remaining.match(regex);
      if (!match || match.index === undefined) {
        tokens.push(remaining);
        break;
      }

      if (match.index > 0) {
        tokens.push(remaining.substring(0, match.index));
      }

      const matchedText = match[0];

      // Bold: **text** or __text__
      if ((matchedText.startsWith('**') && matchedText.endsWith('**')) ||
          (matchedText.startsWith('__') && matchedText.endsWith('__'))) {
        const inner = matchedText.slice(2, -2);
        tokens.push(
          React.createElement('strong', { key: `b-${keyIdx++}`, className: 'editorial-bold' }, inner)
        );
      }
      // Inline Code: `code`
      else if (matchedText.startsWith('`') && matchedText.endsWith('`')) {
        const inner = matchedText.slice(1, -1);
        tokens.push(
          React.createElement('code', { key: `c-${keyIdx++}`, className: 'editorial-code' }, inner)
        );
      }
      // Markdown Link: [text](url)
      else if (matchedText.startsWith('[') && matchedText.includes('](') && matchedText.endsWith(')')) {
        const linkMatch = matchedText.match(/\[([^\]]+)\]\(([^)]+)\)/);
        if (linkMatch) {
          tokens.push(
            React.createElement('a', {
              key: `a-${keyIdx++}`,
              href: linkMatch[2],
              target: '_blank',
              rel: 'noopener noreferrer',
              className: 'editorial-link'
            }, linkMatch[1])
          );
        } else {
          tokens.push(matchedText);
        }
      }
      // Swiss Guillemets: «text»
      else if (matchedText.startsWith('«') && matchedText.endsWith('»')) {
        tokens.push(
          React.createElement('span', { key: `q-${keyIdx++}`, className: 'editorial-guillemet-quote' }, matchedText)
        );
      }
      // Inline Quote: "text"
      else if (matchedText.startsWith('"') && matchedText.endsWith('"') && matchedText.length > 5) {
        tokens.push(
          React.createElement('span', { key: `q-${keyIdx++}`, className: 'editorial-inline-quote' }, matchedText)
        );
      }
      // Italic: *text* or _text_
      else if ((matchedText.startsWith('*') && matchedText.endsWith('*')) ||
               (matchedText.startsWith('_') && matchedText.endsWith('_'))) {
        const inner = matchedText.slice(1, -1);
        tokens.push(
          React.createElement('em', { key: `i-${keyIdx++}`, className: 'editorial-italic' }, inner)
        );
      } else {
        tokens.push(matchedText);
      }

      remaining = remaining.substring(match.index + matchedText.length);
    }

    return tokens;
  };

  // Block-level parsing
  const lines = text.split('\n');
  const blocks = [];
  let currentList = null;
  let currentQuote = [];

  const flushList = (idx) => {
    if (!currentList) return;
    const items = currentList.items.map((item, itemIdx) => (
      React.createElement('li', { key: `li-${idx}-${itemIdx}`, className: 'editorial-list-item' }, renderInline(item))
    ));

    if (currentList.type === 'ul') {
      blocks.push(
        React.createElement('ul', { key: `ul-${idx}`, className: 'editorial-list' }, items)
      );
    } else {
      blocks.push(
        React.createElement('ol', { key: `ol-${idx}`, className: 'editorial-num-list' }, items)
      );
    }
    currentList = null;
  };

  const flushQuote = (idx) => {
    if (currentQuote.length === 0) return;
    const quoteContent = currentQuote.join(' ');
    blocks.push(
      React.createElement('blockquote', { key: `quote-${idx}`, className: 'editorial-pullquote' },
        React.createElement('span', { className: 'pullquote-bar', 'aria-hidden': 'true' }),
        React.createElement('div', { className: 'pullquote-body' },
          React.createElement('p', null, renderInline(quoteContent))
        )
      )
    );
    currentQuote = [];
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();

    // Check for blockquote (> ...)
    if (line.startsWith('>')) {
      if (currentList) flushList(idx);
      const cleanQuote = line.replace(/^>\s*/, '');
      currentQuote.push(cleanQuote);
      return;
    } else if (currentQuote.length > 0) {
      flushQuote(idx);
    }

    // Check for bullet lists
    const isBullet = line.startsWith('- ') || line.startsWith('* ');
    const isNumbered = /^\d+\.\s/.test(line);

    if (isBullet) {
      const itemText = line.replace(/^[-*]\s+/, '');
      if (currentList && currentList.type === 'ul') {
        currentList.items.push(itemText);
      } else {
        if (currentList) flushList(idx);
        currentList = { type: 'ul', items: [itemText] };
      }
      return;
    } else if (isNumbered) {
      const itemText = line.replace(/^\d+\.\s+/, '');
      if (currentList && currentList.type === 'ol') {
        currentList.items.push(itemText);
      } else {
        if (currentList) flushList(idx);
        currentList = { type: 'ol', items: [itemText] };
      }
      return;
    } else if (currentList) {
      flushList(idx);
    }

    // Check for dividers
    if (line === '---' || line === '***' || line === '___') {
      blocks.push(React.createElement('hr', { key: `hr-${idx}`, className: 'editorial-divider' }));
      return;
    }

    // Check for Headings: ####, ###, ##, #
    if (line.startsWith('#### ')) {
      const headingText = line.replace(/^####\s+/, '');
      blocks.push(
        React.createElement('h5', { key: `h5-${idx}`, className: 'editorial-heading editorial-h5' },
          renderInline(headingText)
        )
      );
      return;
    }
    if (line.startsWith('### ')) {
      const headingText = line.replace(/^###\s+/, '');
      blocks.push(
        React.createElement('h4', { key: `h4-${idx}`, className: 'editorial-heading editorial-h4' },
          renderInline(headingText)
        )
      );
      return;
    }
    if (line.startsWith('## ')) {
      const headingText = line.replace(/^##\s+/, '');
      blocks.push(
        React.createElement('h3', { key: `h3-${idx}`, className: 'editorial-heading editorial-h3' },
          renderInline(headingText)
        )
      );
      return;
    }
    if (line.startsWith('# ')) {
      const headingText = line.replace(/^#\s+/, '');
      blocks.push(
        React.createElement('h2', { key: `h2-${idx}`, className: 'editorial-heading editorial-h2' },
          renderInline(headingText)
        )
      );
      return;
    }

    // Normal prose line
    if (line.length > 0) {
      blocks.push(
        React.createElement('p', { key: `p-${idx}`, className: 'editorial-prose-line' },
          renderInline(line)
        )
      );
    }
  });

  // Flush remaining buffers
  if (currentQuote.length > 0) flushQuote(lines.length);
  if (currentList) flushList(lines.length);

  return React.createElement('div', { className: `editorial-markdown-stream ${className}` }, blocks);
}

// Global exposure for in-browser Babel script loading
window.EditorialMarkdown = EditorialMarkdown;
