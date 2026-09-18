import React, { useState } from 'react';
import { Copy, Check, Code as CodeIcon } from 'lucide-react';

const CodeBlock = ({ code, language }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-slate-800 bg-slate-900 text-slate-100 shadow-md">
      <div className="bg-slate-950 px-4 py-2 flex items-center justify-between border-b border-slate-800 text-[11px] text-slate-400 font-mono">
        <span className="flex items-center gap-1.5 font-bold uppercase tracking-wider text-indigo-400">
          <CodeIcon size={13} />
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-slate-400 hover:text-slate-100 bg-slate-800/80 hover:bg-slate-800 px-2 py-1 rounded-md transition-all text-[10px] font-sans font-semibold cursor-pointer"
        >
          {copied ? (
            <>
              <Check size={12} className="text-emerald-400" />
              <span className="text-emerald-400">Copied!</span>
            </>
          ) : (
            <>
              <Copy size={12} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-4 overflow-x-auto font-mono text-xs leading-relaxed text-slate-200">
        <code>{code}</code>
      </pre>
    </div>
  );
};

// Helper function to render text containing bold (**text**) and inline code (`code`)
const renderFormattedInlineText = (text, isUser = false) => {
  if (!text) return null;

  // Split by inline code blocks first: `code`
  const codeParts = text.split(/(`[^`]+`)/g);

  return codeParts.map((codePart, cIdx) => {
    if (codePart.startsWith('`') && codePart.endsWith('`') && codePart.length > 2) {
      const codeContent = codePart.slice(1, -1);
      return (
        <code
          key={cIdx}
          className={`font-mono text-[11px] px-1.5 py-0.5 rounded-md font-semibold border ${
            isUser
              ? 'bg-violet-700/80 text-violet-100 border-violet-500/50'
              : 'bg-indigo-50 text-indigo-700 border-indigo-200/80'
          }`}
        >
          {codeContent}
        </code>
      );
    }

    // Process bold text **text** or __text__ within non-code parts
    const boldParts = codePart.split(/(\*\*[^*]+\*\*|__[^_]+__)/g);
    return boldParts.map((boldPart, bIdx) => {
      if (
        (boldPart.startsWith('**') && boldPart.endsWith('**') && boldPart.length > 4) ||
        (boldPart.startsWith('__') && boldPart.endsWith('__') && boldPart.length > 4)
      ) {
        const boldContent = boldPart.slice(2, -2);
        return (
          <strong key={bIdx} className={isUser ? 'font-bold text-white' : 'font-bold text-gray-900'}>
            {boldContent}
          </strong>
        );
      }
      return boldPart;
    });
  });
};

const FormattedMarkdown = ({ content, isUser = false }) => {
  if (!content) return null;

  // 1. Separate code blocks (```lang ... ```) from rest of text
  const codeBlockRegex = /(```[\s\S]*?```)/g;
  const blocks = content.split(codeBlockRegex);

  return (
    <div className={`space-y-3 leading-relaxed text-xs ${isUser ? 'text-white' : 'text-gray-800'}`}>
      {blocks.map((block, blockIdx) => {
        // Handle Code Blocks
        if (block.startsWith('```') && block.endsWith('```')) {
          const lines = block.slice(3, -3).trim().split('\n');
          let language = 'code';
          let codeText = block.slice(3, -3).trim();

          // Check if first line specifies language (e.g. ```sql)
          if (lines.length > 0 && /^[a-zA-Z0-9_\-\+]+$/.test(lines[0].trim())) {
            language = lines[0].trim();
            codeText = lines.slice(1).join('\n');
          }

          return <CodeBlock key={blockIdx} code={codeText} language={language} />;
        }

        // Process standard text line by line to format lists, headers, and paragraphs
        const lines = block.split('\n');
        const elements = [];
        let currentList = null;

        lines.forEach((line, lIdx) => {
          const trimmed = line.trim();

          if (!trimmed) {
            currentList = null;
            elements.push(<div key={`br-${lIdx}`} className="h-1.5" />);
            return;
          }

          // Headers: ### Header, ## Header, # Header
          const headerMatch = trimmed.match(/^(#{1,3})\s+(.*)$/);
          if (headerMatch) {
            currentList = null;
            const level = headerMatch[1].length;
            const title = headerMatch[2];
            const sizeClass =
              level === 1 ? 'text-base font-extrabold mt-3 mb-1.5' : level === 2 ? 'text-sm font-bold mt-3 mb-1' : 'text-xs font-bold mt-2.5 mb-1';
            elements.push(
              <div key={`h-${lIdx}`} className={`${sizeClass} ${isUser ? 'text-white' : 'text-gray-900'}`}>
                {renderFormattedInlineText(title, isUser)}
              </div>
            );
            return;
          }

          // Numbered list: 1. Item, 2. Item
          const numListMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
          if (numListMatch) {
            const num = numListMatch[1];
            const itemText = numListMatch[2];

            elements.push(
              <div key={`num-${lIdx}`} className="flex items-start gap-2.5 my-1.5 pl-1">
                <span
                  className={`w-5 h-5 rounded-full text-[10px] font-bold shrink-0 flex items-center justify-center mt-0.5 ${
                    isUser ? 'bg-violet-700 text-white' : 'bg-indigo-100 text-indigo-700 border border-indigo-200/80'
                  }`}
                >
                  {num}
                </span>
                <div className="flex-1 leading-relaxed pt-0.5">{renderFormattedInlineText(itemText, isUser)}</div>
              </div>
            );
            return;
          }

          // Bullet list: - Item, * Item
          const bulletListMatch = trimmed.match(/^[\-\*]\s+(.*)$/);
          if (bulletListMatch) {
            const itemText = bulletListMatch[1];

            elements.push(
              <div key={`bullet-${lIdx}`} className="flex items-start gap-2.5 my-1 pl-2">
                <span
                  className={`w-1.5 h-1.5 rounded-full shrink-0 mt-2 ${
                    isUser ? 'bg-white' : 'bg-indigo-500'
                  }`}
                />
                <div className="flex-1 leading-relaxed">{renderFormattedInlineText(itemText, isUser)}</div>
              </div>
            );
            return;
          }

          // Standard paragraph line
          currentList = null;
          elements.push(
            <p key={`p-${lIdx}`} className="leading-relaxed">
              {renderFormattedInlineText(trimmed, isUser)}
            </p>
          );
        });

        return <React.Fragment key={blockIdx}>{elements}</React.Fragment>;
      })}
    </div>
  );
};

export default FormattedMarkdown;
