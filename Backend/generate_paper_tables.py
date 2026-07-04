import json
import csv
from pathlib import Path

RESULTS_DIR = Path("test_results")
RESULTS_FILE = RESULTS_DIR / "all_results.json"
FAILURES_FILE = RESULTS_DIR / "failure_scenarios.json"

def format_latex_table_1(results):
    latex = []
    latex.append(r"\begin{table}[htbp]")
    latex.append(r"\caption{Tree-sitter AST Parsing and Precision/Recall Metrics}")
    latex.append(r"\label{tab:treesitter}")
    latex.append(r"\centering")
    latex.append(r"\begin{tabular}{llcccccc}")
    latex.append(r"\hline")
    latex.append(r"Project & Language & Files & Symbols & Precision & Recall & F1-Score & Time (s) \\")
    latex.append(r"\hline")
    
    for r in results:
        if not r.get("success"):
            continue
        prec = f"{r.get('ts_precision'):.2f}" if r.get('ts_precision') else "N/A"
        rec = f"{r.get('ts_recall'):.2f}" if r.get('ts_recall') else "N/A"
        f1 = f"{r.get('ts_f1'):.2f}" if r.get('ts_f1') else "N/A"
        
        name = r.get("label")
        lang = r.get("language_profile").capitalize()
        files = r.get("source_files_analyzed")
        symbols = r.get("ts_symbols_found")
        time = f"{r.get('processing_time_sec'):.2f}"
        
        latex.append(f"{name} & {lang} & {files} & {symbols} & {prec} & {rec} & {f1} & {time} \\\\")
        
    latex.append(r"\hline")
    latex.append(r"\end{tabular}")
    latex.append(r"\end{table}")
    return "\n".join(latex)

def format_latex_table_2(results):
    latex = []
    latex.append(r"\begin{table}[htbp]")
    latex.append(r"\caption{Mermaid Diagram Structure and Quality Metrics}")
    latex.append(r"\label{tab:mermaid}")
    latex.append(r"\centering")
    latex.append(r"\begin{tabular}{lccccc}")
    latex.append(r"\hline")
    latex.append(r"Project & Valid & Nodes & Edges & Subgraphs & File Ref. Rate \\")
    latex.append(r"\hline")
    
    for r in results:
        if not r.get("success"):
            continue
        valid = "Yes" if r.get("mermaid_valid") else "No"
        ref_rate = f"\\%{r.get('mermaid_file_reference_rate')*100:.0f}"
        
        latex.append(f"{r.get('label')} & {valid} & {r.get('mermaid_node_count')} & {r.get('mermaid_edge_count')} & {r.get('mermaid_subgraph_count')} & {ref_rate} \\\\")
        
    latex.append(r"\hline")
    latex.append(r"\end{tabular}")
    latex.append(r"\end{table}")
    return "\n".join(latex)

def format_latex_table_3(results):
    latex = []
    latex.append(r"\begin{table}[htbp]")
    latex.append(r"\caption{Semantic Filtering (NLP) vs Full AST Analysis (Baseline)}")
    latex.append(r"\label{tab:nlp}")
    latex.append(r"\centering")
    latex.append(r"\begin{tabular}{lccccc}")
    latex.append(r"\hline")
    latex.append(r"Project & Baseline Time (s) & NLP Time (s) & Delay/Diff (s) & Token Reduction & NLP Nodes \\")
    latex.append(r"\hline")
    
    nlp_tested = [r for r in results if r.get("nlp_mode_tested")]
    for r in nlp_tested:
        diff = r.get("nlp_processing_time_sec") - r.get("processing_time_sec")
        diff_str = f"+{diff:.2f}" if diff >= 0 else f"{diff:.2f}"
        reduction = f"\\%{r.get('nlp_token_reduction_pct'):.0f}"
        
        latex.append(f"{r.get('label')} & {r.get('processing_time_sec'):.2f} & {r.get('nlp_processing_time_sec'):.2f} & {diff_str} & {reduction} & {r.get('nlp_mermaid_node_count')} \\\\")
        
    latex.append(r"\hline")
    latex.append(r"\end{tabular}")
    latex.append(r"\end{table}")
    return "\n".join(latex)

def main():
    if not RESULTS_FILE.exists():
        print("Results file not found. Run test_runner.py first.")
        return
        
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    # Generate tables
    t1 = format_latex_table_1(results)
    t2 = format_latex_table_2(results)
    t3 = format_latex_table_3(results)
    
    output_path = RESULTS_DIR / "latex_tables.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("% ==========================================================\n")
        f.write("% TABLE 1: TREE-SITTER METRICS\n")
        f.write("% ==========================================================\n")
        f.write(t1)
        f.write("\n\n")
        f.write("% ==========================================================\n")
        f.write("% TABLE 2: MERMAID DIAGRAM METRICS\n")
        f.write("% ==========================================================\n")
        f.write(t2)
        f.write("\n\n")
        f.write("% ==========================================================\n")
        f.write("% TABLE 3: NLP VS BASELINE COMPARISON\n")
        f.write("% ==========================================================\n")
        f.write(t3)
        f.write("\n")
        
    print(f"LaTeX tables generated at: {output_path.absolute()}")

if __name__ == "__main__":
    main()
