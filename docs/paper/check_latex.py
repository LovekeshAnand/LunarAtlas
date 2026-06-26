import os
import re

paper_tex_path = r"d:\LunarAtlas\docs\paper\main.tex"
paper_bib_path = r"d:\LunarAtlas\docs\paper\paper.bib"

def check_latex_syntax(content):
    errors = []
    
    # Check braces balance
    open_braces = content.count('{')
    close_braces = content.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced curly braces: found {open_braces} '{{' and {close_braces} '}}'.")
        
    # Check math signs balance (simplified)
    # Filter out escaped \$
    stripped_content = content.replace(r'\$', '')
    math_count = stripped_content.count('$')
    if math_count % 2 != 0:
        errors.append(f"Unbalanced '$' signs: found {math_count} math delimiters.")
        
    return errors

def check_figures(content, tex_dir):
    errors = []
    # Find all \includegraphics{path}
    img_matches = re.findall(r'\\includegraphics(?:\[.*?\])?\{(.*?)\}', content)
    
    workspace_root = r"d:\LunarAtlas"
    
    for img_path in img_matches:
        found = False
        # Try resolving exactly, or with common extensions
        for ext in ['', '.png', '.pdf']:
            test_path = img_path + ext
            # Resolve path relative to tex_dir
            full_path = os.path.normpath(os.path.join(tex_dir, test_path))
            # Fallback to resolving relative to workspace root
            if not os.path.exists(full_path):
                fallback_path = os.path.normpath(os.path.join(workspace_root, test_path))
                if os.path.exists(fallback_path):
                    full_path = fallback_path
            
            if os.path.exists(full_path) and not os.path.isdir(full_path):
                print(f"[OK] Figure file exists: {img_path} (resolved to {full_path})")
                found = True
                break
                
        if not found:
            errors.append(f"Figure file not found: '{img_path}'. Checked both PNG and PDF variants.")
            
    return errors

def check_citations(content):
    errors = []
    # Extract citations
    citations = set()
    cite_matches = re.findall(r'\\cite\{(.*?)\}', content)
    for match in cite_matches:
        for key in match.split(','):
            citations.add(key.strip())
            
    # Extract keys from bib file
    bib_keys = set()
    if os.path.exists(paper_bib_path):
        with open(paper_bib_path, 'r', encoding='utf-8') as f:
            bib_content = f.read()
            # Match @type{key, ...
            keys = re.findall(r'@\w+\s*\{\s*([^,\s]+)', bib_content)
            for k in keys:
                bib_keys.add(k.strip())
        print(f"Found {len(bib_keys)} bibliography keys in paper.bib.")
    else:
        errors.append("paper.bib file not found!")
        
    for cite in citations:
        if cite not in bib_keys:
            errors.append(f"Citation key '{cite}' referenced in tex but not found in paper.bib.")
        else:
            print(f"[OK] Citation exists in bib: {cite}")
            
    return errors

def calculate_word_count(content):
    # Remove preamble and end document
    body_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', content, re.DOTALL)
    if not body_match:
        return 0, "No \\begin{document} ... \\end{document} found"
        
    body = body_match.group(1)
    
    # Remove required metadata table
    body = re.sub(r'\\section\*\{Required Metadata\}.*?\\end\{table\}', '', body, flags=re.DOTALL)
    
    # Remove abstract
    body = re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}', '', body, flags=re.DOTALL)
    
    # Remove frontmatter title/authors
    body = re.sub(r'\\begin\{frontmatter\}.*?\\end\{frontmatter\}', '', body, flags=re.DOTALL)
    
    # Remove comments
    body = re.sub(r'%.*?\n', '\n', body)
    
    # Remove LaTeX commands: e.g. \section{...}, \begin{...}, \cite{...}
    # Matches \command[opt]{arg} or \command{arg} or \command
    body = re.sub(r'\\[a-zA-Z]+\*?(?:\[.*?\])?(?:\{.*?\})?', ' ', body)
    
    # Remove math equations in $$ or $
    body = re.sub(r'\$\$.*?\$\$', ' ', body, flags=re.DOTALL)
    body = re.sub(r'\$.*?\$', ' ', body)
    
    # Remove listings environments
    body = re.sub(r'\\begin\{lstlisting\}.*?\\end\{lstlisting\}', ' ', body, flags=re.DOTALL)
    
    # Count words
    words = body.split()
    return len(words)

if __name__ == "__main__":
    if not os.path.exists(paper_tex_path):
        print(f"Error: {paper_tex_path} not found.")
        exit(1)
        
    with open(paper_tex_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()
        
    tex_dir = os.path.dirname(paper_tex_path)
    
    print("=== Running LaTeX Validation ===")
    
    syntax_errors = check_latex_syntax(tex_content)
    if syntax_errors:
        print("\n[FAIL] Syntax Errors:")
        for err in syntax_errors:
            print(f" - {err}")
    else:
        print("[OK] LaTeX syntax checks passed (brackets & math delimiters balanced).")
        
    figure_errors = check_figures(tex_content, tex_dir)
    if figure_errors:
        print("\n[FAIL] Figure Errors:")
        for err in figure_errors:
            print(f" - {err}")
    else:
        print("[OK] All referenced figure paths are valid and exist on disk.")
        
    citation_errors = check_citations(tex_content)
    if citation_errors:
        print("\n[FAIL] Citation Errors:")
        for err in citation_errors:
            print(f" - {err}")
    else:
        print("[OK] All references cited exist in the bibliography database.")
        
    word_count = calculate_word_count(tex_content)
    print(f"\n=== Word Count ===")
    print(f"Body text word count estimate: {word_count} words.")
    if word_count > 4000:
        print(f"[WARNING] Word count exceeds the 4,000-word limit by {word_count - 4000} words.")
    else:
        print("[OK] Word count is within SoftwareX's limit of 4,000 words.")
        
    total_errors = len(syntax_errors) + len(figure_errors) + len(citation_errors)
    print(f"\nTotal errors found: {total_errors}")
    if total_errors > 0:
        exit(1)
    else:
        print("All validations completed successfully!")
        exit(0)
