import React from 'react';

interface EditorialMarkdownProps {
  text: string;
  className?: string;
}

/**
 * EditorialMarkdown: A zero-dependency, high-fidelity markdown parser
 * tailored for Swiss broadsheet journalism (headings, bold, italics, blockquotes, lists).
 */
export const EditorialMarkdown: React.FC<EditorialMarkdownProps> = ({ text, className = '' }) => {
  if (!text) return null;

  // Render inline formatting (bold, italics, code, links, quotes)
  const renderInline = (str: string): React.ReactNode[] => {
    const tokens: React.ReactNode[] = [];
    let remaining = str;
    let keyIdx = 0;

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
          <strong key={`b-${keyIdx++}`} className="editorial-bold">
            {inner}
          </strong>
        );
      }
      // Inline Code: `code`
      else if (matchedText.startsWith('`') && matchedText.endsWith('`')) {
        const inner = matchedText.slice(1, -1);
        tokens.push(
          <code key={`c-${keyIdx++}`} className="editorial-code">
            {inner}
          </code>
        );
      }
      // Markdown Link: [text](url)
      else if (matchedText.startsWith('[') && matchedText.includes('](') && matchedText.endsWith(')')) {
        const linkMatch = matchedText.match(/\[([^\]]+)\]\(([^)]+)\)/);
        if (linkMatch) {
          tokens.push(
            <a
              key={`a-${keyIdx++}`}
              href={linkMatch[2]}
              target="_blank"
              rel="noopener noreferrer"
              className="editorial-link"
            >
              {linkMatch[1]}
            </a>
          );
        } else {
          tokens.push(matchedText);
        }
      }
      // Swiss Guillemets: «text»
      else if (matchedText.startsWith('«') && matchedText.endsWith('»')) {
        tokens.push(
          <span key={`q-${keyIdx++}`} className="editorial-guillemet-quote">
            {matchedText}
          </span>
        );
      }
      // Quotation in quotes: "text"
      else if (matchedText.startsWith('"') && matchedText.endsWith('"') && matchedText.length > 5) {
        tokens.push(
          <span key={`q-${keyIdx++}`} className="editorial-inline-quote">
            {matchedText}
          </span>
        );
      }
      // Italic: *text* or _text_
      else if ((matchedText.startsWith('*') && matchedText.endsWith('*')) ||
               (matchedText.startsWith('_') && matchedText.endsWith('_'))) {
        const inner = matchedText.slice(1, -1);
        tokens.push(
          <em key={`i-${keyIdx++}`} className="editorial-italic">
            {inner}
          </em>
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
  const blocks: React.ReactNode[] = [];
  let currentList: { type: 'ul' | 'ol'; items: string[] } | null = null;
  let currentQuote: string[] = [];

  const flushList = (idx: number) => {
    if (!currentList) return;
    const items = currentList.items.map((item, itemIdx) => (
      <li key={`li-${idx}-${itemIdx}`} className="editorial-list-item">
        {renderInline(item)}
      </li>
    ));

    if (currentList.type === 'ul') {
      blocks.push(
        <ul key={`ul-${idx}`} className="editorial-list">
          {items}
        </ul>
      );
    } else {
      blocks.push(
        <ol key={`ol-${idx}`} className="editorial-num-list">
          {items}
        </ol>
      );
    }
    currentList = null;
  };

  const flushQuote = (idx: number) => {
    if (currentQuote.length === 0) return;
    const quoteContent = currentQuote.join(' ');
    blocks.push(
      <blockquote key={`quote-${idx}`} className="editorial-pullquote">
        <span className="pullquote-bar" aria-hidden="true"></span>
        <div className="pullquote-body">
          <p>{renderInline(quoteContent)}</p>
        </div>
      </blockquote>
    );
    currentQuote = [];
  };

  lines.forEach((rawLine, idx) => {
    const line = rawLine.trim();

    // Check for quotes (> ...)
    if (line.startsWith('>')) {
      if (currentList) flushList(idx);
      const cleanQuote = line.replace(/^>\s*/, '');
      currentQuote.push(cleanQuote);
      return;
    } else if (currentQuote.length > 0) {
      flushQuote(idx);
    }

    // Check for lists
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
      blocks.push(<hr key={`hr-${idx}`} className="editorial-divider" />);
      return;
    }

    // Check for Headings: ####, ###, ##, #
    if (line.startsWith('#### ')) {
      const headingText = line.replace(/^####\s+/, '');
      blocks.push(
        <h5 key={`h5-${idx}`} className="editorial-heading editorial-h5">
          {renderInline(headingText)}
        </h5>
      );
      return;
    }
    if (line.startsWith('### ')) {
      const headingText = line.replace(/^###\s+/, '');
      blocks.push(
        <h4 key={`h4-${idx}`} className="editorial-heading editorial-h4">
          {renderInline(headingText)}
        </h4>
      );
      return;
    }
    if (line.startsWith('## ')) {
      const headingText = line.replace(/^##\s+/, '');
      blocks.push(
        <h3 key={`h3-${idx}`} className="editorial-heading editorial-h3">
          {renderInline(headingText)}
        </h3>
      );
      return;
    }
    if (line.startsWith('# ')) {
      const headingText = line.replace(/^#\s+/, '');
      blocks.push(
        <h2 key={`h2-${idx}`} className="editorial-heading editorial-h2">
          {renderInline(headingText)}
        </h2>
      );
      return;
    }

    // Normal prose line
    if (line.length > 0) {
      blocks.push(
        <p key={`p-${idx}`} className="editorial-prose-line">
          {renderInline(line)}
        </p>
      );
    }
  });

  // Flush remaining buffers
  if (currentQuote.length > 0) flushQuote(lines.length);
  if (currentList) flushList(lines.length);

  return <div className={`editorial-markdown-stream ${className}`}>{blocks}</div>;
};

export default EditorialMarkdown;
