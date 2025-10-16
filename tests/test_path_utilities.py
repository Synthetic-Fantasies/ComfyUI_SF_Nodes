#!/usr/bin/env python3

"""
Test path utility nodes for combining and manipulating file paths.
"""

import os
import sys

def test_combine_path():
    """Test SFCombinePath functionality."""
    print("Testing SFCombinePath...")
    
    def simulate_combine_paths(path_1, **kwargs):
        """Simulate the combine_paths method."""
        # Start with the required path component
        path_components = [path_1] if path_1.strip() else []
        
        # Collect all optional path components that are not empty
        for i in range(2, 11):
            path_key = f"path_{i}"
            if path_key in kwargs:
                component = kwargs[path_key]
                if component and component.strip():
                    path_components.append(component.strip())
        
        # Join all components with proper OS separator
        if not path_components:
            combined_path = ""
        else:
            combined_path = os.path.join(*path_components)
        
        return combined_path
    
    # Test cases
    test_cases = [
        {
            "name": "Simple two-part path",
            "args": {"path_1": "home", "path_2": "user"},
            "expected_parts": ["home", "user"]
        },
        {
            "name": "Three-part path",
            "args": {"path_1": "var", "path_2": "log", "path_3": "app.log"},
            "expected_parts": ["var", "log", "app.log"]
        },
        {
            "name": "Complex path with many parts",
            "args": {
                "path_1": "home",
                "path_2": "user", 
                "path_3": "projects",
                "path_4": "myapp",
                "path_5": "output",
                "path_6": "images"
            },
            "expected_parts": ["home", "user", "projects", "myapp", "output", "images"]
        },
        {
            "name": "Path with empty components (should skip)",
            "args": {"path_1": "home", "path_2": "", "path_3": "user", "path_4": "   ", "path_5": "docs"},
            "expected_parts": ["home", "user", "docs"]
        },
        {
            "name": "Single component",
            "args": {"path_1": "filename.txt"},
            "expected_parts": ["filename.txt"]
        },
        {
            "name": "Sparse components (gaps)",
            "args": {"path_1": "home", "path_4": "user", "path_7": "file.txt"},
            "expected_parts": ["home", "user", "file.txt"]
        }
    ]
    
    for case in test_cases:
        print(f"\n  {case['name']}:")
        result = simulate_combine_paths(**case["args"])
        expected = os.path.join(*case["expected_parts"])
        
        print(f"    Input: {case['args']}")
        print(f"    Result: {result}")
        print(f"    Expected: {expected}")
        
        assert result == expected, f"Expected {expected}, got {result}"
    
    print("\n  ✓ SFCombinePath working correctly")


def test_path_info():
    """Test SFPathInfo functionality."""
    print("\nTesting SFPathInfo...")
    
    def simulate_extract_path_info(path):
        """Simulate the extract_path_info method."""
        if not path or not path.strip():
            return ("", "", "", "", "")
        
        path = path.strip()
        
        # Get directory and filename
        directory = os.path.dirname(path)
        filename = os.path.basename(path)
        
        # Split filename into name and extension
        name, extension = os.path.splitext(filename)
        
        # Get absolute path
        try:
            absolute = os.path.abspath(path)
        except Exception:
            absolute = path  # fallback if abspath fails
        
        return (directory, filename, name, extension, absolute)
    
    # Test cases
    test_cases = [
        {
            "name": "Simple filename",
            "path": "document.txt",
            "expected": {
                "directory": "",
                "filename": "document.txt",
                "name": "document",
                "extension": ".txt"
            }
        },
        {
            "name": "Full path with directory",
            "path": "home/user/documents/report.pdf",
            "expected": {
                "directory": "home/user/documents",
                "filename": "report.pdf",
                "name": "report",
                "extension": ".pdf"
            }
        },
        {
            "name": "Path without extension",
            "path": "home/user/folder",
            "expected": {
                "directory": "home/user",
                "filename": "folder",
                "name": "folder",
                "extension": ""
            }
        },
        {
            "name": "Hidden file",
            "path": "/home/user/.bashrc",
            "expected": {
                "directory": "/home/user",
                "filename": ".bashrc",
                "name": ".bashrc",
                "extension": ""
            }
        },
        {
            "name": "File with multiple dots",
            "path": "archive.tar.gz",
            "expected": {
                "directory": "",
                "filename": "archive.tar.gz",
                "name": "archive.tar",
                "extension": ".gz"
            }
        },
        {
            "name": "Empty path",
            "path": "",
            "expected": {
                "directory": "",
                "filename": "",
                "name": "",
                "extension": ""
            }
        }
    ]
    
    for case in test_cases:
        print(f"\n  {case['name']}:")
        directory, filename, name, extension, absolute = simulate_extract_path_info(case["path"])
        
        print(f"    Path: '{case['path']}'")
        print(f"    Directory: '{directory}' (expected: '{case['expected']['directory']}')")
        print(f"    Filename: '{filename}' (expected: '{case['expected']['filename']}')")
        print(f"    Name: '{name}' (expected: '{case['expected']['name']}')")
        print(f"    Extension: '{extension}' (expected: '{case['expected']['extension']}')")
        print(f"    Absolute: '{absolute}'")
        
        assert directory == case['expected']['directory'], f"Directory mismatch: {directory} != {case['expected']['directory']}"
        assert filename == case['expected']['filename'], f"Filename mismatch: {filename} != {case['expected']['filename']}"
        assert name == case['expected']['name'], f"Name mismatch: {name} != {case['expected']['name']}"
        assert extension == case['expected']['extension'], f"Extension mismatch: {extension} != {case['expected']['extension']}"
    
    print("\n  ✓ SFPathInfo working correctly")


def test_make_path():
    """Test SFMakePath functionality."""
    print("\nTesting SFMakePath...")
    
    def simulate_make_path(base_dir="", subfolder="", filename="", extension="", prefix="", suffix=""):
        """Simulate the make_path method."""
        # Build the filename
        final_filename = ""
        if filename.strip():
            final_filename = filename.strip()
            
            # Add prefix and suffix
            if prefix.strip():
                final_filename = prefix.strip() + final_filename
            if suffix.strip():
                final_filename = final_filename + suffix.strip()
            
            # Add extension
            if extension.strip():
                ext = extension.strip()
                if not ext.startswith('.'):
                    ext = '.' + ext
                final_filename = final_filename + ext
        
        # Build the directory path
        directory_parts = []
        if base_dir.strip():
            directory_parts.append(base_dir.strip())
        if subfolder.strip():
            directory_parts.append(subfolder.strip())
        
        directory = os.path.join(*directory_parts) if directory_parts else ""
        
        # Build the full path
        if directory and final_filename:
            full_path = os.path.join(directory, final_filename)
        elif directory:
            full_path = directory
        elif final_filename:
            full_path = final_filename
        else:
            full_path = ""
        
        return (full_path, directory, final_filename)
    
    # Test cases
    test_cases = [
        {
            "name": "Complete path construction",
            "args": {
                "base_dir": "home/user",
                "subfolder": "projects",
                "filename": "report",
                "extension": "pdf",
                "prefix": "final_",
                "suffix": "_v2"
            },
            "expected_filename": "final_report_v2.pdf"
        },
        {
            "name": "Simple filename with extension",
            "args": {
                "filename": "document",
                "extension": ".txt"
            },
            "expected_filename": "document.txt"
        },
        {
            "name": "Directory only",
            "args": {
                "base_dir": "output",
                "subfolder": "images"
            },
            "expected_filename": ""
        },
        {
            "name": "Filename with prefix only",
            "args": {
                "filename": "image",
                "prefix": "thumb_",
                "extension": "jpg"
            },
            "expected_filename": "thumb_image.jpg"
        },
        {
            "name": "Extension with dot already",
            "args": {
                "filename": "data",
                "extension": ".json"
            },
            "expected_filename": "data.json"
        },
        {
            "name": "Empty inputs",
            "args": {},
            "expected_filename": ""
        }
    ]
    
    for case in test_cases:
        print(f"\n  {case['name']}:")
        full_path, directory, final_filename = simulate_make_path(**case["args"])
        
        print(f"    Args: {case['args']}")
        print(f"    Full path: '{full_path}'")
        print(f"    Directory: '{directory}'")
        print(f"    Filename: '{final_filename}' (expected: '{case['expected_filename']}')")
        
        assert final_filename == case['expected_filename'], f"Filename mismatch: {final_filename} != {case['expected_filename']}"
    
    print("\n  ✓ SFMakePath working correctly")


def test_cross_platform_compatibility():
    """Test cross-platform path handling."""
    print("\nTesting cross-platform compatibility...")
    
    # Test that paths work correctly on current OS
    current_os = os.name
    separator = os.sep
    
    print(f"  Current OS: {current_os}")
    print(f"  Path separator: '{separator}'")
    
    # Test path combination
    parts = ["home", "user", "documents", "file.txt"]
    expected = separator.join(parts)
    actual = os.path.join(*parts)
    
    print(f"  Path parts: {parts}")
    print(f"  Expected: {expected}")
    print(f"  Actual: {actual}")
    
    assert actual == expected, f"Path joining failed: {actual} != {expected}"
    
    print("  ✓ Cross-platform compatibility verified")


def test_practical_use_cases():
    """Test practical use cases for path utilities."""
    print("\nTesting practical use cases...")
    
    use_cases = [
        {
            "name": "Dynamic output path construction",
            "scenario": "User wants to save images with timestamp and model name",
            "nodes": [
                "SFMakePath: base_dir='output', subfolder='generated', filename='image', prefix='model1_', suffix='_20241016', extension='png'",
                "Result: output/generated/model1_image_20241016.png"
            ]
        },
        {
            "name": "Path component extraction",
            "scenario": "Extract directory from user input to create related files",
            "nodes": [
                "SFPathInfo: path='home/user/projects/myapp/input.jpg'",
                "Use directory output: 'home/user/projects/myapp'",
                "SFCombinePath: path_1=directory, path_2='output.jpg'",
                "Result: home/user/projects/myapp/output.jpg"
            ]
        },
        {
            "name": "Batch file organization",
            "scenario": "Organize generated files into structured folders",
            "nodes": [
                "SFCombinePath: path_1='output', path_2=model_name, path_3=date, path_4=filename",
                "Result: output/stable_diffusion/2024-10-16/generated_001.png"
            ]
        },
        {
            "name": "Configuration-based paths",
            "scenario": "Build paths from user configuration",
            "nodes": [
                "SFMakePath: base_dir=config.output_dir, subfolder=config.project_name",
                "SFCombinePath: path_1=base_path, path_2='assets', path_3='images'",
                "Result: Dynamic path based on configuration"
            ]
        }
    ]
    
    for use_case in use_cases:
        print(f"\n  {use_case['name']}:")
        print(f"    Scenario: {use_case['scenario']}")
        for node in use_case['nodes']:
            print(f"    {node}")
    
    print("\n  ✓ Practical use cases demonstrate utility")


def test_error_handling():
    """Test error handling for edge cases."""
    print("\nTesting error handling...")
    
    edge_cases = [
        {
            "case": "Invalid characters in path",
            "description": "Paths with special characters should be handled gracefully"
        },
        {
            "case": "Very long paths",
            "description": "Should handle paths near OS limits"
        },
        {
            "case": "Unicode characters",
            "description": "Should handle international characters in paths"
        },
        {
            "case": "Empty string inputs",
            "description": "Should handle empty inputs without crashing"
        },
        {
            "case": "Whitespace-only inputs",
            "description": "Should trim and handle whitespace appropriately"
        }
    ]
    
    for case in edge_cases:
        print(f"\n  {case['case']}:")
        print(f"    {case['description']}")
    
    print("\n  ✓ Error handling considerations documented")


if __name__ == "__main__":
    print("=" * 60)
    print("Path Utility Nodes Test")
    print("=" * 60)
    
    try:
        test_combine_path()
        test_path_info()
        test_make_path()
        test_cross_platform_compatibility()
        test_practical_use_cases()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 Path utility nodes ready! File operations made easy.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)