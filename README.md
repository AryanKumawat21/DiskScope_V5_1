# DiskScope V5.1 — Modern Disk Space Analyzer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)]()
[![Type](https://img.shields.io/badge/Project-OS%20Mini%20Project-orange.svg)]()

**DiskScope** is a lightweight, responsive desktop disk space analysis and file management utility developed in **Python 3** with a custom dark-themed **Tkinter** GUI. It scans storage drives and directories recursively, visualizes storage distribution through dynamic percentage bar charts, lists large space-consuming files, and enables direct file management actions.

Designed specifically as an **Operating Systems (OS) Mini Project**, it illustrates core systems programming concepts such as multi-threaded non-blocking GUI execution, hierarchical directory traversal, filesystem metadata retrieval, and error resilience against restricted system paths.

---

## 📌 Key Features

- **⚡ Multi-Threaded Scanning (Zero GUI Freezes)**  
  Executes background directory traversal using Python's `threading` module and a synchronized `queue.Queue`. The UI remains fully responsive and interactive during large drive scans.

- **📊 Folder Usage Visualization**  
  Displays horizontal storage percentage bars and exact sizes for folders inside the analyzed path, making storage hogs instantly recognizable.

- **📁 Hierarchical Folder Breakdown**  
  Presents a structured, sortable tree view detailing folder paths, cumulative sizes, and file counts.

- **🔍 Files & Actions Management Hub**  
  - Identifies largest individual files consuming disk space.
  - **Open File:** Launch files directly in their default system application on double-click or button press.
  - **Open Containing Folder:** Jump directly to the file's directory in Windows Explorer.
  - **Move & Delete:** Safely move files to another directory or permanently delete unwanted files (with explicit confirmation modals to prevent accidental loss).

- **🧭 Real-Time Location Breadcrumbs**  
  Keeps full context of the currently selected scan root with quick "Open in Explorer" access.

- **💾 CSV Report Export**  
  Export complete scan results (folder paths, sizes, and file metrics) to structured CSV files for auditing or reporting.

- **🎨 Modern Dark UI Theme**  
  Styled with a high-contrast dark palette (`#0b1220`) and custom styled Tkinter/TTK widgets.

- **📦 Zero External Dependencies**  
  Runs on pure Python standard libraries (`tkinter`, `os`, `shutil`, `threading`, `queue`, `csv`). No `pip install` required.

---

## 🖥️ Operating Systems Concepts Demonstrated

This project is tailored for academic evaluation, OS lab practicals, and viva discussions:

| OS Concept | Implementation in DiskScope |
| :--- | :--- |
| **Directory Traversal** | Recursive filesystem tree traversal using `os.walk` to enumerate nodes. |
| **Filesystem Hierarchy** | Managing hierarchical paths, parent-child relationships, and directory depths. |
| **File Metadata Extraction** | Accessing file descriptors, sizes (`os.path.getsize`), and timestamps. |
| **Storage Aggregation** | Computing cumulative storage allocations across nested folder hierarchies. |
| **Concurrency & Threading** | Offloading I/O-intensive scanning to a background worker thread (`threading.Thread`). |
| **Inter-Thread Communication**| Synchronizing worker status and GUI updates safely via thread-safe queues (`queue.Queue`). |
| **File Operations & I/O** | Direct filesystem manipulations including file opening, moving (`shutil.move`), and removal (`os.remove`). |
| **Fault Tolerance & Safety** | Handling OS-level exceptions (`PermissionError`, `FileNotFoundError`) when traversing protected system directories. |

---

## 📂 Project Structure

```text
DiskScope_V5_1/
├── diskscope.py          # Main application source code (Tkinter GUI + Scanner engine)
├── run_windows.bat       # One-click Windows launch script
├── requirements.txt      # Dependency specification (pure standard library)
├── PROJECT_SYNOPSIS.md   # Project abstract & viva reference sheet
├── README.md             # Complete documentation
└── .gitignore            # Git configuration ignoring cache & temporary files
```

---

## 🚀 How to Run

### Prerequisites
- Windows OS (7 / 10 / 11)
- Python 3.8 or higher installed with Tkinter support (standard Python Windows installer includes Tkinter by default).
- Ensure **"Add Python to PATH"** was checked during Python installation.

### Method 1: Using the Launcher Batch Script (Recommended)
Double-click `run_windows.bat` in the project root directory.

### Method 2: Via Command Prompt / PowerShell
Open a terminal in the project directory and run:
```bash
python diskscope.py
```

---

## 📖 Usage Guide

1. **Select Location:** Choose a drive letter from the dropdown or click **"Browse folder"** to pick any specific directory.
2. **Analyze:** Click the **"▶ Analyze"** button. The progress bar will indicate active scanning while the status updates in real-time.
3. **Explore Results via Tabs:**
   - **Folder Breakdown:** Double-click any folder to open it directly in Windows Explorer.
   - **Files & Actions:** View large files, double-click to open, or select a file to use the Move/Delete actions.
   - **Folder Usage:** View proportional horizontal bar charts showing which subfolders consume the most percentage of the scanned root.
4. **Export:** Click **"Export CSV"** to save the complete breakdown for documentation or offline analysis.

---

## ⚠️ Safety Notice

- **Delete Action:** Deletion through the application removes files permanently from the filesystem (`os.remove`). Always test actions on sample/test folders first.
- **Scanning Safety:** Scans are completely read-only and do not alter or lock existing files.

---

## 📝 Changelog (V5.1 Hotfix)

- Fixed a Tkinter callback reference error from legacy canvas pointers during scan reset.
- Streamlined full-width tab navigation buttons for seamless switching.
- Refined Folder Usage horizontal percentage bar rendering.
- Added double-click handlers for quick Explorer and file-launch operations.
- Updated breadcrumb bar with active path monitoring and Explorer shortcuts.

---

## 📄 License

This project is open-source and intended for educational and academic use. Feel free to use and adapt it for learning and project submissions.
