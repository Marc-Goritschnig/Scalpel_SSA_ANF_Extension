import { ApplicationConfig } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import {HIGHLIGHT_OPTIONS} from "ngx-highlightjs";

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    {
      provide: HIGHLIGHT_OPTIONS,
      useValue: {
        coreLibraryLoader: () => import('highlight.js/lib/core'),
        lineNumbersLoader: () => import('ngx-highlightjs/line-numbers'), // Optional, only if you want the line numbers
        languages: {
          python: () => import('highlight.js/lib/languages/python')
        }
      }
    }
    ]
};
