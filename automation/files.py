import os
import shutil
import logging
from typing import Dict, Any, List

logger = logging.getLogger("assistant.automation.files")

class FileAutomation:
    def __init__(self, notes_dir: str = "output/notes"):
        self.notes_dir = notes_dir
        if not os.path.exists(self.notes_dir):
            os.makedirs(self.notes_dir)

    def resolve_path(self, path_str: str, default_parent: str = "desktop") -> str:
        r"""Resolves system paths, drive letters (C:\, D:\), user shortcuts (Desktop, Documents), and relative paths."""
        if not path_str:
            return self.get_user_path(default_parent)
            
        clean_path = path_str.strip().strip("'\"")
        
        # Check for drive letter or absolute path
        if len(clean_path) >= 2 and clean_path[1] == ":" or os.path.isabs(clean_path) or clean_path.startswith("~"):
            return os.path.abspath(os.path.expanduser(clean_path))
            
        # Check for standard folder keywords
        lower = clean_path.lower()
        if lower in ["desktop", "documents", "downloads", "pictures", "music"]:
            return self.get_user_path(lower)
            
        # Default to relative inside parent folder
        parent_path = self.get_user_path(default_parent)
        return os.path.abspath(os.path.join(parent_path, clean_path))

    def get_user_path(self, folder_name: str) -> str:
        """Resolves user profile folders on Windows (Desktop, Documents, Downloads, Pictures, Music)."""
        home = os.path.expanduser("~")
        folder = (folder_name or "").lower().strip()
        
        if "desktop" in folder:
            return os.path.join(home, "Desktop")
        elif "document" in folder:
            return os.path.join(home, "Documents")
        elif "download" in folder:
            return os.path.join(home, "Downloads")
        elif "picture" in folder or "image" in folder:
            return os.path.join(home, "Pictures")
        elif "music" in folder or "audio" in folder:
            return os.path.join(home, "Music")
        else:
            return home

    def open_folder(self, folder_name: str) -> Dict[str, Any]:
        """Opens a standard system folder in Windows Explorer."""
        path = self.resolve_path(folder_name)
        try:
            logger.info("Opening folder: %s (%s)", folder_name, path)
            if os.path.exists(path):
                os.startfile(path)
                return {"success": True, "message": f"Opened folder '{path}'."}
            else:
                return {"success": False, "message": f"Folder '{path}' does not exist."}
        except Exception as e:
            logger.error("Failed to open folder %s: %s", path, e)
            return {"success": False, "message": f"Could not open folder. Error: {str(e)}"}

    def create_folder(self, name: str, parent_folder: str = "desktop", path: str = "") -> Dict[str, Any]:
        """Creates a new folder or nested subfolders at the target location or specified path."""
        try:
            # Determine target directory path
            if path and len(path.strip()) > 0:
                target_path = self.resolve_path(path)
                # If name is provided and not already at the end of path
                if name and not target_path.lower().endswith(name.lower()):
                    target_path = os.path.join(target_path, name)
            else:
                parent_path = self.get_user_path(parent_folder)
                target_path = os.path.join(parent_path, name)

            # Create folder and any parent subdirectories recursively
            os.makedirs(target_path, exist_ok=True)
            logger.info("Created folder: %s", target_path)
            return {"success": True, "message": f"Successfully created folder at: {target_path}"}
        except Exception as e:
            logger.error("Failed to create folder: %s", e)
            return {"success": False, "message": f"Failed to create folder. Error: {str(e)}"}

    def create_file(self, filename: str, content: str = "", parent_folder: str = "desktop", path: str = "") -> Dict[str, Any]:
        """Creates a file of any type (.py, .java, .c, .cpp, .html, .css, .js, .json, .sql, .txt, .xlsx, .pptx, etc.) at specified path."""
        try:
            # Determine target file path
            if path and len(path.strip()) > 0:
                resolved_dir = self.resolve_path(path)
                if filename and not resolved_dir.lower().endswith(filename.lower()):
                    target_path = os.path.join(resolved_dir, filename)
                else:
                    target_path = resolved_dir
            else:
                parent_path = self.get_user_path(parent_folder)
                target_path = os.path.join(parent_path, filename)

            # Ensure parent directories exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            # Write file content
            ext = os.path.splitext(target_path)[1].lower()
            if ext in [".xlsx", ".pptx", ".docx"]:
                # For office binary extensions without third-party heavy tools, write formatted text/CSV fallback if string
                with open(target_path, "wb" if isinstance(content, bytes) else "w", encoding=None if isinstance(content, bytes) else "utf-8") as f:
                    f.write(content if content else f"# Created by Jarvis Assistant: {os.path.basename(target_path)}")
            else:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(content)

            logger.info("Created file: %s", target_path)
            return {"success": True, "message": f"Successfully created file '{os.path.basename(target_path)}' at: {target_path}"}
        except Exception as e:
            logger.error("Failed to create file: %s", e)
            return {"success": False, "message": f"Failed to create file. Error: {str(e)}"}

    def create_multiple_folders(self, folder_names: List[str], parent_folder: str = "desktop", path: str = "") -> Dict[str, Any]:
        """Creates multiple folders in a single action."""
        created = []
        failed = []
        for f_name in folder_names:
            clean_name = f_name.strip()
            if not clean_name:
                continue
            res = self.create_folder(name=clean_name, parent_folder=parent_folder, path=path)
            if res.get("success"):
                created.append(clean_name)
            else:
                failed.append(clean_name)
        
        msg = f"Created {len(created)} folder(s): {', '.join(created)}."
        if failed:
            msg += f" Failed: {', '.join(failed)}."
        return {"success": len(failed) == 0, "message": msg}

    def create_multiple_files(self, file_list: List[Dict[str, str]], parent_folder: str = "desktop", path: str = "") -> Dict[str, Any]:
        """Creates multiple files in a single action."""
        created = []
        failed = []
        for item in file_list:
            if isinstance(item, str):
                fname = item.strip()
                content = ""
            elif isinstance(item, dict):
                fname = (item.get("filename") or item.get("name") or "").strip()
                content = item.get("content", "")
            else:
                continue

            if not fname:
                continue

            res = self.create_file(filename=fname, content=content, parent_folder=parent_folder, path=path)
            if res.get("success"):
                created.append(fname)
            else:
                failed.append(fname)

        msg = f"Created {len(created)} file(s): {', '.join(created)}."
        if failed:
            msg += f" Failed: {', '.join(failed)}."
        return {"success": len(failed) == 0, "message": msg}

    def rename_file(self, old_name: str, new_name: str, parent_folder: str = "desktop") -> Dict[str, Any]:
        """Renames a file or folder in a specified directory."""
        parent_path = self.get_user_path(parent_folder)
        old_path = os.path.join(parent_path, old_name)
        new_path = os.path.join(parent_path, new_name)
        try:
            if not os.path.exists(old_path):
                return {"success": False, "message": f"File '{old_name}' not found on {parent_folder}."}
            os.rename(old_path, new_path)
            logger.info("Renamed %s to %s", old_path, new_path)
            return {"success": True, "message": f"Renamed '{old_name}' to '{new_name}'."}
        except Exception as e:
            logger.error("Failed to rename file: %s", e)
            return {"success": False, "message": f"Failed to rename. Error: {str(e)}"}

    def delete_file(self, filename: str, parent_folder: str = "desktop", confirmed: bool = False) -> Dict[str, Any]:
        """Deletes a file or directory, requiring confirmation for safety."""
        if not confirmed:
            logger.warning("Deletion attempted without confirmation for: %s", filename)
            return {
                "success": False, 
                "requires_confirmation": True, 
                "message": f"To delete '{filename}', please confirm your action."
            }

        parent_path = self.get_user_path(parent_folder)
        target_path = os.path.join(parent_path, filename)
        try:
            if not os.path.exists(target_path):
                return {"success": False, "message": f"File '{filename}' does not exist on {parent_folder}."}
                
            if os.path.isdir(target_path):
                shutil.rmtree(target_path)
            else:
                os.remove(target_path)
            logger.info("Deleted file/folder: %s", target_path)
            return {"success": True, "message": f"Successfully deleted '{filename}'."}
        except Exception as e:
            logger.error("Failed to delete file %s: %s", target_path, e)
            return {"success": False, "message": f"Failed to delete. Error: {str(e)}"}

    def write_note(self, title: str, content: str) -> Dict[str, Any]:
        """Writes a text note to the notes folder."""
        # Clean title for filename
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in " _-"]).rstrip()
        if not safe_title:
            safe_title = "note"
            
        filename = f"{safe_title}.txt"
        target_path = os.path.join(self.notes_dir, filename)
        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Wrote note to: %s", target_path)
            return {"success": True, "message": f"Note '{title}' saved successfully."}
        except Exception as e:
            logger.error("Failed to save note: %s", e)
            return {"success": False, "message": f"Failed to save note. Error: {str(e)}"}

    def read_note(self, title: str) -> Dict[str, Any]:
        """Reads a note from the notes folder."""
        safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c in " _-"]).rstrip()
        filename = f"{safe_title}.txt"
        target_path = os.path.join(self.notes_dir, filename)
        try:
            if not os.path.exists(target_path):
                return {"success": False, "message": f"Note '{title}' not found."}
            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info("Read note: %s", target_path)
            return {"success": True, "content": content}
        except Exception as e:
            logger.error("Failed to read note: %s", e)
            return {"success": False, "message": f"Failed to read note. Error: {str(e)}"}
            
    def list_notes(self) -> List[str]:
        """Lists all saved notes titles."""
        try:
            files = os.listdir(self.notes_dir)
            return [os.path.splitext(f)[0] for f in files if f.endswith(".txt")]
        except Exception as e:
            logger.error("Failed to list notes: %s", e)
            return []

    def read_document_file(self, filename_or_path: str, max_chars: int = 3000) -> Dict[str, Any]:
        """Reads content from a PDF document or text file (.pdf, .txt, .md, .py, .csv, .json, .log)."""
        try:
            target_path = self.resolve_path(filename_or_path)
            if not os.path.exists(target_path):
                # Search desktop/documents/downloads for filename match
                for folder in ["desktop", "documents", "downloads"]:
                    alt_path = os.path.join(self.get_user_path(folder), filename_or_path)
                    if os.path.exists(alt_path):
                        target_path = alt_path
                        break

            if not os.path.exists(target_path):
                return {"success": False, "message": f"File '{filename_or_path}' could not be found."}

            ext = os.path.splitext(target_path)[1].lower()

            if ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(target_path)
                    text_content = ""
                    for page in reader.pages[:10]: # Read up to 10 pages
                        page_text = page.extract_text() or ""
                        text_content += page_text + "\n"

                    clean_text = text_content.strip()
                    if not clean_text:
                        return {"success": False, "message": f"PDF file '{os.path.basename(target_path)}' has no readable text content."}
                    
                    snippet = clean_text[:max_chars]
                    return {
                        "success": True, 
                        "filename": os.path.basename(target_path),
                        "total_pages": len(reader.pages),
                        "content": snippet,
                        "message": f"Read PDF document '{os.path.basename(target_path)}' ({len(reader.pages)} pages). Content snippet:\n\n{snippet}"
                    }
                except Exception as e:
                    return {"success": False, "message": f"Error reading PDF file: {str(e)}"}
            else:
                # Read text / code document
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()

                clean_text = text_content.strip()
                snippet = clean_text[:max_chars]
                return {
                    "success": True,
                    "filename": os.path.basename(target_path),
                    "content": snippet,
                    "message": f"Read file '{os.path.basename(target_path)}'. Content snippet:\n\n{snippet}"
                }
        except Exception as e:
            logger.error("Failed to read document file %s: %s", filename_or_path, e)
            return {"success": False, "message": f"Failed to read document. Error: {str(e)}"}
            
    def search_local_files(self, query: str, parent_folder: str = "desktop") -> List[str]:
        """Simple recursive search for files in standard directory."""
        path = self.get_user_path(parent_folder)
        matched = []
        try:
            # Look at top 3 levels max to avoid hanging on large directories
            for root, dirs, files in os.walk(path):
                # Calculate depth
                depth = root[len(path):].count(os.sep)
                if depth > 2:
                    continue
                for f in files:
                    if query.lower() in f.lower():
                        matched.append(os.path.join(root, f))
                for d in dirs:
                    if query.lower() in d.lower():
                        matched.append(os.path.join(root, d))
                if len(matched) >= 10: # Limit output count
                    break
            return matched[:10]
        except Exception as e:
            logger.error("Search files failed: %s", e)
            return []
