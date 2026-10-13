import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MarkdownRendererTest(unittest.TestCase):
    def test_gfm_table_is_rendered_as_semantic_table(self):
        script = textwrap.dedent(
            f"""
            class FakeNode {{
              constructor(tagName, text='') {{
                this.tagName = tagName;
                this.className = '';
                this.children = [];
                this.attributes = {{}};
                this._text = text;
              }}
              append(...items) {{ this.children.push(...items); }}
              setAttribute(name, value) {{ this.attributes[name] = value; }}
            }}
            global.document = {{
              createElement: tag => new FakeNode(tag),
              createTextNode: text => new FakeNode('#text', text),
            }};
            const {{ renderMarkdown }} = require({str(ROOT / 'static' / 'markdown.js')!r});
            const root = renderMarkdown(`### AWS 스토리지 서비스 구별

| 서비스 | 용도 |
|---|---|
| **S3** | 객체 스토리지 |
| EBS | EC2 블록 스토리지 |

표 다음 문단입니다.`);
            const tableWrap = root.children[1];
            const table = tableWrap.children[0];
            const text = node => node._text + node.children.map(text).join('');
            const result = {{
              heading: root.children[0].tagName,
              wrapperClass: tableWrap.className,
              table: table.tagName,
              headCells: table.children[0].children[0].children.map(text),
              bodyRows: table.children[1].children.length,
              boldCell: table.children[1].children[0].children[0].children[0].tagName,
              paragraph: text(root.children[2]),
            }};
            process.stdout.write(JSON.stringify(result));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script], cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout,
            '{"heading":"h4","wrapperClass":"markdown-table-wrap","table":"table",'
            '"headCells":["서비스","용도"],"bodyRows":2,"boldCell":"strong",'
            '"paragraph":"표 다음 문단입니다."}',
        )


if __name__ == "__main__":
    unittest.main()
