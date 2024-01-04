import {Component, ViewChild} from '@angular/core';
import {CommonModule} from '@angular/common';
import {RouterOutlet} from '@angular/router';
import {HighlightModule} from "ngx-highlightjs";

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, HighlightModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'CodeComparator';

  @ViewChild('code1') code1: any;
  @ViewChild('code2') code2: any;
  @ViewChild('code3') code3: any;

  public pyCodeBefore = '';
  public pyCodeHighlighted = '';
  public pyCodeAfter = '';

  public pyCode = '';
  public pyCodeLines: Array<string> = [];

  public anfCode = '';
  public anfCodeLines: Array<string> = [];
  public wordCollection: Array<Array<Word>> = [];

  constructor() {

  }

  onFileChange(event: any): void {
    const file = event.target.files[0];

    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.parseFile(e.target.result);
        event.target.value = null;
      };

      reader.readAsText(file);
    }
  }


  hoveredOver(w: Word, words: Word[], idx: number) {

    // Highlight first word in line if the indentation is hovered
    if (idx === 0 && w.text.match('^(&nbsp;)+?')) {
      console.log('replace');
      w = words[1];
    }

    let codeElement = document.getElementById('code');

    if (codeElement) {
      if (w.pos.lineno === 0) {
        codeElement.innerHTML = this.pyCode;
      } else {

        const indentation = this.pyCodeLines[w.pos.lineno - 1].match('^ +');

        let txtHighlighted = '';
        let txtBefore = '';
        let txtAfter = '';

        // Collect code before highlighted section
        if (w.pos.lineno > 1) {
          txtBefore += this.pyCodeLines.slice(0, w.pos.lineno - 1).join('\n') + '\n';
        }
        if (w.pos.col_offset > 0) {
          txtBefore += this.pyCodeLines[w.pos.lineno - 1].slice(0, w.pos.col_offset);
        }


        // Collect highlighted code
        if (w.pos.lineno === w.pos.end_lineno) {
          txtHighlighted += this.pyCodeLines[w.pos.lineno - 1].slice(w.pos.col_offset, w.pos.end_col_offset);
        } else {
          // Add part of first line to be highlighted
          txtHighlighted += this.pyCodeLines[w.pos.lineno - 1].slice(w.pos.col_offset, this.pyCodeLines[w.pos.lineno - 1].length) + '\n';
          // Add full lines between start and end of section highlighted
          if (w.pos.lineno < w.pos.end_lineno - 1) {
            txtHighlighted += this.pyCodeLines.slice(w.pos.lineno, w.pos.end_lineno - 1).join('\n') + '\n';
          }
          // Add part of last line to be highlighted
          txtHighlighted += this.pyCodeLines[w.pos.end_lineno - 1].slice(0, w.pos.end_col_offset);
        }

        if (indentation) {
          // Remove indentation corresponding to col_offset because inline block css is used
          let i = 0;
          let lines: string[] = [];

          console.log('cut off');
          console.log(w);
          console.log(txtHighlighted);
          for (const line of txtHighlighted.split('\n')) {
            if (i === 0) {
              lines.push(line);
              i++;
              continue;
            }
            lines.push(line.slice(indentation[0].length));
            i++;
          }
          txtHighlighted = lines.join('\n');
          console.log(txtHighlighted);
        }

        // Collect code after highlighted section
        console.log(w);
        console.log(w.pos.end_col_offset, this.pyCodeLines[w.pos.end_lineno - 1].length);
        if (w.pos.end_col_offset < this.pyCodeLines[w.pos.end_lineno - 1].length - 1) {
          txtAfter += this.pyCodeLines[w.pos.end_lineno - 1].slice(w.pos.end_col_offset, this.pyCodeLines[w.pos.lineno - 1].length);
          console.log(txtAfter);
        }
        if (w.pos.end_lineno < this.pyCodeLines.length) {
          txtAfter += '\n' + this.pyCodeLines.slice(w.pos.end_lineno, this.pyCodeLines.length).join('\n');
          console.log(txtAfter);
        }
        console.log(txtBefore);
        console.log(txtHighlighted);
        console.log(txtAfter);

        this.pyCodeBefore = txtBefore;
        this.pyCodeHighlighted = txtHighlighted;
        this.pyCodeAfter = txtAfter;

        codeElement.innerHTML = txtBefore + '<span class="highlight">' + txtHighlighted + '</span>' + txtAfter;

      }
    }
  }

  private parseFile(code: string) {

    const fileParts = code.split('\r\n##########\r\n');

    this.pyCode = fileParts[0];
    this.pyCodeLines = this.pyCode.split('\n');
    this.anfCode = fileParts[1];
    this.anfCodeLines = this.anfCode.split('\n');
    this.wordCollection = [];

    for (const line of this.anfCodeLines) {

      if (line.match('^( )*#.*')){
        let comm = line.substring(0, line.lastIndexOf('--'));
        this.wordCollection.push([new Word(comm, new Position(null))]);
        continue;
      }

      let wordsBuffer = [];
      const indentation = line.match('^ *');
      if (indentation && indentation[0]) {
        wordsBuffer.push(new Word('&nbsp;'.repeat(indentation[0].length), new Position(null)));
      }

      const info = line.trim().split('--')[1];
      const words = line.trim().split('--')[0].trim().split(' ');
      const positions = [];

      const info_parts = info.split('|');
      for (const infoPart of info_parts) {
        const parts = infoPart.split(';');
        if (parts.length > 1) {
          positions.push(new Position(parts[1]));
        } else {
          positions.push(new Position(null));
        }
      }

      let i = 0;
      for (const w of words) {
        wordsBuffer.push(new Word(w, positions[i]));
        i++;
      }
      this.wordCollection.push(wordsBuffer);
    }

  }

  keywords = ['let', 'letrec', '=', 'in', 'if', 'else', 'then'];

  isKeyWord(w: Word) {
    return this.keywords.indexOf(w.text) > -1;
  }
  isFunCall(w: Word) {
    return w.text.startsWith('_') && !w.text.startsWith('_SSA') && w.text != '_';
  }
  isBlockLabel(w: Word) {
    return w.text.match('L(\\d)+');
  }
  isBufferVariable(w: Word) {
    return w.text.startsWith('%');
  }
  isConstant(w: Word) {
    return w.text.match('^\\d+?') || w.text == 'True' || w.text == 'False';
  }
  isComment(w: Word) {
    return w.text.match('^( )*#.*');
  }
  isString(w: Word) {
    return w.text.match('\\\'.*\\\'');
  }
}

class Word {
  public text = '';
  public pos: Position;

  constructor(text: string, pos: Position) {
    this.text = text;
    this.pos = pos;
  }

}

class Position {
  public lineno = 0;
  public col_offset = 0;
  public end_lineno = 0;
  public end_col_offset = 0;

  constructor(pos_string: string | null) {
    if (pos_string && pos_string !== '') {
      const borders = pos_string.split(',');
      const start = borders[0].split(':');
      const end = borders[1].split(':');

      this.lineno = +start[0];
      this.col_offset = +start[1];
      this.end_lineno = +end[0];
      this.end_col_offset = +end[1];
    }
  }
}
