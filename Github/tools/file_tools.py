@@
 def write_file(path:str, content:str):
@@
-    try:
-
-
-        file_path=safe_path(path)
-
-
-
-        file_path.parent.mkdir(
-
-            parents=True,
-
-            exist_ok=True
-
-        )
-
-
-
-        file_path.write_text(
-
-            content,
-
-            encoding="utf-8"
-
-        )
-
-
-
-        return f"Saved: {path}"
-
-
-
-    except Exception as e:
-
-
-        return f"WRITE ERROR: {e}"
+    try:
+
+        # FIX1: Basic heuristic check to avoid writing JSON action objects as file content
+        if isinstance(content, str):
+            c = content.strip()
+            if re.match(r'^\s*\{\s*["\']?(name|action|type)["\']?\s*:', c) or re.match(r'^\s*\[\s*\{\s*["\']?(name|action|type)["\']?\s*:', c):
+                return "WRITE REJECTED: content appears to be a JSON action object; file content must be raw file text."
+
+        file_path=safe_path(path)
+
+
+
+        file_path.parent.mkdir(
+
+            parents=True,
+
+            exist_ok=True
+
+        )
+
+
+
+        file_path.write_text(
+
+            content,
+
+            encoding="utf-8"
+
+        )
+
+
+
+        return f"Saved: {path}"
+
+
+
+    except Exception as e:
+
+
+        return f"WRITE ERROR: {e}"
