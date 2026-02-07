import json
from pathlib import Path
from pdf_reader import structurize
from pipeline import process_document

def main():
    try:
        # Get file path from user
        file_path = input("Enter the File Path: ").strip()
        
        if not file_path:
            print("Error: No file path provided.")
            return
        
        # Step 1: Structure the PDF
        print(f"Processing PDF: {file_path}")
        doc_structure = structurize(file_path)
        
        if doc_structure is None:
            print("Failed to process PDF. Exiting.")
            return
        
        # Check if we have any content
        if not doc_structure.get("chapters"):
            print("Warning: No chapters or content found in the PDF.")
        
        # Step 2: Process through pipeline
        print("Running document through compression pipeline...")
        try:
            result = process_document(doc_structure)
            
            # Step 3: Save output
            output_path = "output.json"
            try:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"Success! Compressed output saved to: {output_path}")
                
                # Print summary statistics
                if result.get("analysis", {}).get("document_summary"):
                    summary = result["analysis"]["document_summary"]
                    print("\n=== Compression Summary ===")
                    for key, items in summary.items():
                        print(f"{key.capitalize()}: {len(items)} items")
                    
                    # Show explainability stats
                    if result.get("explainability", {}).get("statistics"):
                        stats = result["explainability"]["statistics"]
                        print(f"\nTotal chapters: {stats.get('total_chapters', 0)}")
                        print(f"Total items retained: {stats.get('total_items', 0)}")
                        
            except (IOError, PermissionError) as e:
                print(f"Error saving output file: {str(e)}")
                # Print result to console if file save fails
                print("\n=== Compressed Output ===")
                print(json.dumps(result, indent=2)[:1000] + "...")
                
        except Exception as pipeline_error:
            print(f"Error in pipeline processing: {str(pipeline_error)}")
            import traceback
            traceback.print_exc()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Unexpected error in main: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()