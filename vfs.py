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
        self._vfs_tree: Dict[str, Any] = {}  # внутреннее представление VFS
        self._current_path: List[str] = []   # текущий путь как список имён (например: ['home', 'user'])
        self._xml_sha256: str = ""

        self._load_vfs()


    # загружает и парсит XML-файл VFS.
    def _load_vfs(self):
        
        try:
            with open(self._vfs_xml_path, 'rb') as f:
                xml_data = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"VFS XML файл не найден: {self._vfs_xml_path}")

        
        self._xml_sha256 = hashlib.sha256(xml_data).hexdigest()# SHA-256 хеш содержимого файла

        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            raise ValueError(f"Неверный формат XML: {e}")

        if root.tag != 'vfs':
            raise ValueError("Корневой элемент XML должен быть <vfs>")

        self._root_name = root.get('name', 'unnamed_vfs')
        self._vfs_tree = self._parse_node(root)

    def _parse_node(self, element: ET.Element) -> Dict[str, Any]:
        
        # рекурсивно парсит XML-элемент в словарь.
        
        node = {'type': 'dir', 'children': {}}

        for child in element:
            name = child.get('name')
            if not name:
                continue

            if child.tag == 'dir':
                node['children'][name] = self._parse_node(child)
            elif child.tag == 'file':
                # данные файла могут быть в base64 (или пустыми)
                content = child.text.strip() if child.text else ""
                try:
                    if content:
                        base64.b64decode(content, validate=True)
                except Exception:
                    pass
                node['children'][name] = {'type': 'file', 'content': content}
            

        return node
    
    # возвращает информацию о VFS для команды vfs-info.
    def get_vfs_info(self) -> str:
        
        return f"VFS Name: {self._root_name}\nSHA-256: {self._xml_sha256}\n"
    
    # возвращает узел по пути (список имён).
    def _get_node_at_path(self, path_parts: List[str]) -> Optional[Dict[str, Any]]:
        
        node = self._vfs_tree
        
        # пустой путь = корень VFS
        if not path_parts:
            return node
        
        for part in path_parts:
            if node['type'] != 'dir':
                return None
            if part not in node['children']:
                return None
            node = node['children'][part]
        return node

    # смена текущей директории.  '.', '..', и абсолютные пути.
    def cd(self, path: str) -> str:
        
        
        if path.startswith('/'):
            # абсолютный путь - начинаем с корня
            if path == '/':
                target_parts = []  # корень VFS
            else:
                target_parts = [p for p in path[1:].split('/') if p and p != '.']
        else:
            # относительный путь от текущей директории
            target_parts = self._current_path + [p for p in path.split('/') if p and p != '.']
        
        # обработка '..'
        resolved = []
        for part in target_parts:
            if part == '..':
                if resolved:  # Если есть куда возвращаться
                    resolved.pop()
                # Если resolved пуст - остаемся в корне (это нормально)
            else:
                resolved.append(part)
        
        #проверка существования пути
        node = self._get_node_at_path(resolved)
        if not node:
            # формирование читаемого пути для сообщения об ошибке
            abs_path = '/' + '/'.join(resolved) if resolved else '/'
            return f"Ошибка: директория не найдена: {abs_path}\n"
        
        if node['type'] != 'dir':
            abs_path = '/' + '/'.join(resolved) if resolved else '/'
            return f"Ошибка: путь не является директорией: {abs_path}\n"
        
        # если путь  корректен - обновляем текущий путь
        self._current_path = resolved
        return ""


    # возвращает список файлов и директорий в текущей директории.
    def ls(self) -> str:
        
        node = self._get_node_at_path(self._current_path)
        if not node or node['type'] != 'dir':
            return "Ошибка: текущая директория недоступна\n"

        names = sorted(node['children'].keys())
        if not names:
            return ""
        return "\n".join(names) + "\n"
    

    # возвращает текущий путь в виде абсолютного пути (например: /home/user или /).
    def get_current_path_str(self) -> str:
        
        if not self._current_path:
            return "/"
        return "/" + "/".join(self._current_path)
    

    def read_file(self, path: str) -> str:
        
        # читает содержимое файла по относительному или абсолютному пути.
        # возвращает содержимое (декодированное из base64, если возможно), либо вызывает исключение.
        
        if path.startswith('/'):
            if path == '/':
                raise ValueError("Невозможно прочитать корень как файл")
            target_parts = [p for p in path[1:].split('/') if p and p != '.']
        else:
            target_parts = self._current_path + [p for p in path.split('/') if p and p != '.']

        # обработка '..'
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
                # попытка декодировать base64
                decoded = base64.b64decode(content, validate=True)
                return decoded.decode('utf-8')
            except Exception:
                # если не base64 — возвращаем как есть (предполагаем текст)
                return content
        return ""
    
    #-------------------------------------------------------5--------------------------------------------------------
    def mkdir(self, path: str) -> str:
        # cоздает директорию по указанному пути.
        # путь может быть абсолютным или относительным.
        
        if path.startswith('/'):
            if path == '/':
                return "Ошибка: невозможно создать корневую директорию\n"
            target_parts = [p for p in path[1:].split('/') if p and p != '.']
        else:
            target_parts = self._current_path + [p for p in path.split('/') if p and p != '.']
        
        # обработка '..'
        resolved = []
        for part in target_parts:
            if part == '..':
                if resolved:
                    resolved.pop()
            else:
                resolved.append(part)
        
        # проверяем, не пытаемся ли создать существующую директорию
        existing_node = self._get_node_at_path(resolved)
        if existing_node:
            abs_path = '/' + '/'.join(resolved) if resolved else '/'
            return f"Ошибка: директория уже существует: {abs_path}\n"
        
        # создаем директорию рекурсивно
        try:
            self._create_directory_recursive(resolved)
            return ""
        except Exception as e:
            return f"Ошибка создания директории: {e}\n"
    
    def _create_directory_recursive(self, path_parts: List[str]) -> None:
        """Рекурсивно создает директории по указанному пути"""
        current_node = self._vfs_tree
        
        for part in path_parts:
            if current_node['type'] != 'dir':
                raise ValueError("Промежуточный путь не является директорией")
            
            if part not in current_node['children']:
                # создаем новую директорию
                current_node['children'][part] = {'type': 'dir', 'children': {}}
            
            current_node = current_node['children'][part]




    
    def cp(self, source: str, destination: str) -> str:
        
        # копирует файл из source в destination.
        # поддерживает только копирование файлов (не директорий).
        
        # получает исходный файл
        if source.startswith('/'):
            source_parts = [p for p in source[1:].split('/') if p and p != '.']
        else:
            source_parts = self._current_path + [p for p in source.split('/') if p and p != '.']
        
        # обработка '..' для source
        resolved_source = []
        for part in source_parts:
            if part == '..':
                if resolved_source:
                    resolved_source.pop()
            else:
                resolved_source.append(part)
        
        source_node = self._get_node_at_path(resolved_source)
        if not source_node:
            abs_source = '/' + '/'.join(resolved_source) if resolved_source else '/'
            return f"Ошибка: исходный файл не найден: {abs_source}\n"
        
        if source_node['type'] != 'file':
            abs_source = '/' + '/'.join(resolved_source) if resolved_source else '/'
            return f"Ошибка: исходный путь не является файлом: {abs_source}\n"
        
        # обрабатывает путь назначения
        if destination.startswith('/'):
            dest_parts = [p for p in destination[1:].split('/') if p and p != '.']
        else:
            dest_parts = self._current_path + [p for p in destination.split('/') if p and p != '.']
        
        # обработка '..' для destination
        resolved_dest = []
        for part in dest_parts:
            if part == '..':
                if resolved_dest:
                    resolved_dest.pop()
            else:
                resolved_dest.append(part)
        
        # если destination - директория, используем исходное имя файла
        dest_node = self._get_node_at_path(resolved_dest)
        if dest_node and dest_node['type'] == 'dir':
            filename = resolved_source[-1]  # берем имя файла из source
            resolved_dest.append(filename)
            dest_node = None  # сбрасываем, т.к. путь изменился
        
        # проверяет, не перезаписываем ли существующий файл
        existing_dest = self._get_node_at_path(resolved_dest)
        if existing_dest:
            abs_dest = '/' + '/'.join(resolved_dest) if resolved_dest else '/'
            return f"Ошибка: файл назначения уже существует: {abs_dest}\n"
        
        # копируем файл
        try:
            self._copy_file(resolved_source, resolved_dest, source_node)
            return ""
        except Exception as e:
            return f"Ошибка копирования: {e}\n"
    
    def _copy_file(self, source_parts: List[str], dest_parts: List[str], source_node: Dict[str, Any]) -> None:
        # копирует файл из source_parts в dest_parts
        # создаем директории для пути назначения
        parent_dest_parts = dest_parts[:-1]
        filename = dest_parts[-1]
        
        current_node = self._vfs_tree
        
        # проходим по пути назначения (кроме последнего элемента - имени файла)
        for part in parent_dest_parts:
            if current_node['type'] != 'dir':
                raise ValueError("Промежуточный путь не является директорией")
            
            if part not in current_node['children']:
                raise ValueError(f"Директория назначения не существует: {part}")
            
            current_node = current_node['children'][part]
        
        # создаем копию файла
        if current_node['type'] != 'dir':
            raise ValueError("Путь назначения не является директорией")
        
        current_node['children'][filename] = {
            'type': 'file',
            'content': source_node['content']
        }

