# vfs.py
import xml.etree.ElementTree as ET
import hashlib
import base64
from typing import Optional, List, Dict, Any

class VFSManager:
    def __init__(self, vfs_xml_path: str):
        """
        Инициализирует VFS из XML-файла.
        
        :param vfs_xml_path: Путь к XML-файлу с описанием VFS.
        :raises FileNotFoundError: если файл не найден.
        :raises ValueError: если XML повреждён или не соответствует ожидаемой структуре.
        """
        self._vfs_xml_path = vfs_xml_path
        self._root_name: str = ""
        self._vfs_tree: Dict[str, Any] = {}  # Внутреннее представление VFS
        self._current_path: List[str] = []   # Текущий путь как список имён (например: ['home', 'user'])
        self._xml_sha256: str = ""

        self._load_vfs()


    #Загружает и парсит XML-файл VFS.
    def _load_vfs(self):
        
        try:
            with open(self._vfs_xml_path, 'rb') as f:
                xml_data = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"VFS XML файл не найден: {self._vfs_xml_path}")

        #SHA-256 хеш содержимого файла
        self._xml_sha256 = hashlib.sha256(xml_data).hexdigest()

        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            raise ValueError(f"Неверный формат XML: {e}")

        if root.tag != 'vfs':
            raise ValueError("Корневой элемент XML должен быть <vfs>")

        self._root_name = root.get('name', 'unnamed_vfs')
        self._vfs_tree = self._parse_node(root)

    def _parse_node(self, element: ET.Element) -> Dict[str, Any]:
        """
        Рекурсивно парсит XML-элемент в словарь.
        Поддерживает <dir> и <file>.
        """
        node = {'type': 'dir', 'children': {}}

        for child in element:
            name = child.get('name')
            if not name:
                continue

            if child.tag == 'dir':
                node['children'][name] = self._parse_node(child)
            elif child.tag == 'file':
                # Данные файла могут быть в base64 (или пустыми)
                content = child.text.strip() if child.text else ""
                try:
                    # Попытка декодировать base64 (не обязательно использовать сейчас)
                    if content:
                        base64.b64decode(content, validate=True)
                except Exception:
                    # Не критично на данном этапе — можно оставить как есть
                    pass
                node['children'][name] = {'type': 'file', 'content': content}
            

        return node
    
    #Возвращает информацию о VFS для команды vfs-info.
    def get_vfs_info(self) -> str:
        
        return f"VFS Name: {self._root_name}\nSHA-256: {self._xml_sha256}\n"
    
    #Возвращает узел по пути (список имён).
    def _get_node_at_path(self, path_parts: List[str]) -> Optional[Dict[str, Any]]:
        
        node = self._vfs_tree
        
        # Пустой путь = корень VFS
        if not path_parts:
            return node
        
        for part in path_parts:
            if node['type'] != 'dir':
                return None
            if part not in node['children']:
                return None
            node = node['children'][part]
        return node

    #Смена текущей директории. Поддерживает '.', '..', и абсолютные пути.
    def cd(self, path: str) -> str:
        
        
        if path.startswith('/'):
            # Абсолютный путь - начинаем с корня
            if path == '/':
                target_parts = []  # Корень VFS
            else:
                target_parts = [p for p in path[1:].split('/') if p and p != '.']
        else:
            # Относительный путь - от текущей директории
            target_parts = self._current_path + [p for p in path.split('/') if p and p != '.']
        
        # Обработка '..'
        resolved = []
        for part in target_parts:
            if part == '..':
                if resolved:  # Если есть куда возвращаться
                    resolved.pop()
                # Если resolved пуст - остаемся в корне (это нормально)
            else:
                resolved.append(part)
        
        # Проверяем существование пути
        node = self._get_node_at_path(resolved)
        if not node:
            # Формируем читаемый путь для сообщения об ошибке
            abs_path = '/' + '/'.join(resolved) if resolved else '/'
            return f"Ошибка: директория не найдена: {abs_path}\n"
        
        if node['type'] != 'dir':
            abs_path = '/' + '/'.join(resolved) if resolved else '/'
            return f"Ошибка: путь не является директорией: {abs_path}\n"
        
        # Путь корректен - обновляем текущий путь
        self._current_path = resolved
        return ""


    #Возвращает список файлов и директорий в текущей директории.
    def ls(self) -> str:
        
        node = self._get_node_at_path(self._current_path)
        if not node or node['type'] != 'dir':
            return "Ошибка: текущая директория недоступна\n"

        names = sorted(node['children'].keys())
        if not names:
            return ""
        return "\n".join(names) + "\n"
    

    #Возвращает текущий путь в виде абсолютного пути (например: /home/user или /).
    def get_current_path_str(self) -> str:
        
        if not self._current_path:
            return "/"
        return "/" + "/".join(self._current_path)
    

    def read_file(self, path: str) -> str:
        """
        читает содержимое файла по относительному или абсолютному пути.
        Возвращает содержимое (декодированное из base64, если возможно), либо вызывает исключение.
        """
        if path.startswith('/'):
            if path == '/':
                raise ValueError("Невозможно прочитать корень как файл")
            target_parts = [p for p in path[1:].split('/') if p and p != '.']
        else:
            target_parts = self._current_path + [p for p in path.split('/') if p and p != '.']

        # Обработка '..'
        resolved = []
        for part in target_parts:
            if part == '..':
                if resolved:
                    resolved.pop()
            else:
                resolved.append(part)

        node = self._vfs_tree
        for part in resolved:
            if node['type'] != 'dir' or part not in node['children']:
                raise FileNotFoundError(f"Файл не найден: /{'/'.join(resolved)}")
            node = node['children'][part]

        if node['type'] != 'file':
            raise ValueError(f"Путь не является файлом: /{'/'.join(resolved)}")

        content = node['content']
        if content:
            try:
                # Попытка декодировать base64
                decoded = base64.b64decode(content, validate=True)
                return decoded.decode('utf-8')
            except Exception:
                # Если не base64 — возвращаем как есть (предполагаем текст)
                return content
        return ""

