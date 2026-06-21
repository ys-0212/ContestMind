import logging
import httpx
from bs4 import BeautifulSoup
from typing import Tuple, List, Dict, Optional

logger = logging.getLogger(__name__)

class ScraperService:
    @staticmethod
    def scrape_problem(problem_id: str) -> Optional[Tuple[str, List[Dict[str, str]]]]:
        """
        Scrapes a Codeforces problem by its ID (e.g. 2224A).
        Returns a tuple: (html_statement, examples_list)
        """
        import re
        m = re.match(r"^(\d+)([A-Za-z][A-Za-z0-9]*)$", problem_id.strip().upper())
        if not m:
            return None
            
        contest_id, index = m.group(1), m.group(2)
        url = f"https://codeforces.com/problemset/problem/{contest_id}/{index}"
        
        try:
            import cloudscraper
            scraper = cloudscraper.create_scraper(browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            })
            response = scraper.get(url, timeout=15.0)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to fetch CF problem {problem_id}: {e}")
            return None
            
        soup = BeautifulSoup(response.text, "lxml")
        
        statement_div = soup.find("div", class_="problem-statement")
        if not statement_div:
            logger.error(f"Could not find problem-statement div for {problem_id}")
            return None
            
        # 1. Remove the header (Title, Time limits, etc) as our frontend already shows this
        header = statement_div.find("div", class_="header")
        if header:
            header.decompose()
            
        # 2. Extract Examples
        examples = []
        sample_tests_div = statement_div.find("div", class_="sample-test")
        
        if sample_tests_div:
            # Codeforces structure:
            # <div class="input"><div class="title">Input</div><pre>...</pre></div>
            # <div class="output"><div class="title">Output</div><pre>...</pre></div>
            inputs = sample_tests_div.find_all("div", class_="input")
            outputs = sample_tests_div.find_all("div", class_="output")
            
            for inp, out in zip(inputs, outputs):
                # We want the text inside the <pre> tag. CF sometimes uses <br> or <div> inside <pre>.
                # .get_text(separator="\n") handles <br> well.
                inp_pre = inp.find("pre")
                out_pre = out.find("pre")
                
                if inp_pre and out_pre:
                    in_text = inp_pre.get_text(separator="\n").strip()
                    out_text = out_pre.get_text(separator="\n").strip()
                    examples.append({"input": in_text, "output": out_text})
                    
            # Now remove the entire sample-tests block from the HTML so it doesn't duplicate in the body
            sample_tests_parent = sample_tests_div.parent
            if sample_tests_parent and "sample-tests" in sample_tests_parent.get("class", []):
                sample_tests_parent.decompose()
            else:
                # Codeforces sometimes just wraps it in <div class="sample-tests">
                # wait, let's find the section title "Example" or "Examples" and decompose the wrapper
                wrapper = statement_div.find("div", class_="sample-tests")
                if wrapper:
                    wrapper.decompose()
                else:
                    sample_tests_div.decompose()
                    
        # 3. Clean up the HTML
        # We replace the outer div with just its inner contents, or keep it as a string
        # Codeforces heavily uses $$$ for MathJax. We just return the raw HTML string.
        
        html_content = str(statement_div)
        
        return html_content, examples
