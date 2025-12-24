"""
Diagram Generator for Video Analyzer.
Generates Mermaid diagrams (sequence, flowchart) and ASCII wireframes from video analysis.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FlowNode:
    """Represents a node in a user flow diagram."""
    id: str
    label: str
    node_type: str  # "screen", "action", "decision", "start", "end"
    
    def to_mermaid(self) -> str:
        """Convert to Mermaid node syntax."""
        safe_label = self.label.replace('"', "'").replace('\n', ' ')
        
        if self.node_type == "start":
            return f'{self.id}(("{safe_label}"))'
        elif self.node_type == "end":
            return f'{self.id}(("{safe_label}"))'
        elif self.node_type == "decision":
            return f'{self.id}{{"{safe_label}"}}'
        elif self.node_type == "action":
            return f'{self.id}[/"{safe_label}"/]'
        else:  # screen
            return f'{self.id}["{safe_label}"]'


@dataclass
class FlowEdge:
    """Represents an edge in a user flow diagram."""
    from_node: str
    to_node: str
    label: Optional[str] = None
    
    def to_mermaid(self) -> str:
        """Convert to Mermaid edge syntax."""
        if self.label:
            safe_label = self.label.replace('"', "'")
            return f'{self.from_node} -->|"{safe_label}"| {self.to_node}'
        return f'{self.from_node} --> {self.to_node}'


class DiagramGenerator:
    """
    Generates various diagrams from video analysis data.
    
    Supports:
    - Sequence diagrams (Mermaid)
    - User flow diagrams (Mermaid flowchart)
    - ASCII wireframes
    """
    
    def __init__(self):
        """Initialize diagram generator."""
        self.kroki_url = "https://kroki.io"
        logger.info("DiagramGenerator initialized")
    
    def generate_sequence_diagram(
        self,
        user_flows: List[Dict[str, Any]],
        transcript_segments: Optional[List[Dict]] = None,
        app_name: str = "App"
    ) -> str:
        """
        Generate a Mermaid sequence diagram from user flows.
        
        Args:
            user_flows: List of user flow dictionaries with steps
            transcript_segments: Optional transcript segments for context
            app_name: Name of the application (will be cleaned and truncated)
            
        Returns:
            Mermaid syntax string for sequence diagram
        """
        logger.info(f"Generating sequence diagram from {len(user_flows)} flows")
        
        # Clean and truncate app name for diagram readability
        clean_app_name = self._extract_app_name(app_name)
        
        lines = ["sequenceDiagram"]
        lines.append(f"    participant U as Utente")
        lines.append(f"    participant App as {clean_app_name}")
        lines.append(f"    participant DB as Sistema")
        lines.append("")
        
        for flow in user_flows:
            flow_name = flow.get('name', 'Flusso')
            lines.append(f"    Note over U,DB: {self._safe_mermaid_text(flow_name)}")
            
            steps = flow.get('steps', [])
            for step in steps:
                action = step.get('action', '')
                timestamp = step.get('timestamp', '')
                outcome = step.get('outcome', '')
                
                if not action:
                    continue
                
                # Determine direction based on action keywords
                action_lower = action.lower()
                
                if any(word in action_lower for word in ['clicca', 'seleziona', 'inserisce', 'preme', 'trascina', 'apre']):
                    # User action to App
                    lines.append(f"    U->>App: {self._safe_mermaid_text(action)}")
                    if outcome:
                        lines.append(f"    App-->>U: {self._safe_mermaid_text(outcome)}")
                elif any(word in action_lower for word in ['mostra', 'visualizza', 'carica', 'aggiorna']):
                    # App response to User
                    lines.append(f"    App->>U: {self._safe_mermaid_text(action)}")
                elif any(word in action_lower for word in ['salva', 'conferma', 'invia']):
                    # User action that involves backend
                    lines.append(f"    U->>App: {self._safe_mermaid_text(action)}")
                    lines.append(f"    App->>DB: Salva dati")
                    lines.append(f"    DB-->>App: Conferma")
                    if outcome:
                        lines.append(f"    App-->>U: {self._safe_mermaid_text(outcome)}")
                else:
                    # Generic action
                    lines.append(f"    U->>App: {self._safe_mermaid_text(action)}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_user_flow_diagram(
        self,
        user_flows: List[Dict[str, Any]],
        modules: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Generate a Mermaid flowchart from user flows.
        
        Args:
            user_flows: List of user flow dictionaries
            modules: Optional list of modules for context
            
        Returns:
            Mermaid syntax string for flowchart
        """
        logger.info(f"Generating user flow diagram from {len(user_flows)} flows")
        
        lines = ["flowchart TD"]
        lines.append("")
        
        # Start node
        lines.append("    Start([Inizio])")
        
        node_counter = 0
        previous_node = "Start"
        added_nodes = set(["Start"])
        
        for flow_idx, flow in enumerate(user_flows):
            flow_name = flow.get('name', f'Flusso {flow_idx + 1}')
            steps = flow.get('steps', [])
            
            if not steps:
                continue
            
            # Create subgraph for each flow
            flow_id = f"flow{flow_idx}"
            lines.append(f"    subgraph {flow_id} [{self._safe_mermaid_text(flow_name)}]")
            
            flow_first_node = None
            
            for step_idx, step in enumerate(steps):
                action = step.get('action', f'Azione {step_idx + 1}')
                timestamp = step.get('timestamp', '')
                
                node_counter += 1
                node_id = f"N{node_counter}"
                
                # Determine node type based on action
                action_lower = action.lower()
                if '?' in action or any(word in action_lower for word in ['sceglie', 'decide', 'seleziona se']):
                    node_type = "decision"
                elif any(word in action_lower for word in ['visualizza', 'mostra', 'apre']):
                    node_type = "screen"
                else:
                    node_type = "action"
                
                # Create node
                node = FlowNode(node_id, action[:50], node_type)
                lines.append(f"        {node.to_mermaid()}")
                added_nodes.add(node_id)
                
                if flow_first_node is None:
                    flow_first_node = node_id
                
                # Connect to previous node in this flow
                if step_idx > 0:
                    prev_step_node = f"N{node_counter - 1}"
                    edge = FlowEdge(prev_step_node, node_id)
                    lines.append(f"        {edge.to_mermaid()}")
            
            lines.append("    end")
            lines.append("")
            
            # Connect previous flow/start to this flow
            if flow_first_node:
                lines.append(f"    {previous_node} --> {flow_first_node}")
                # Update previous node to last node of this flow
                previous_node = f"N{node_counter}"
        
        # End node
        lines.append(f"    {previous_node} --> EndNode([Fine])")
        
        return "\n".join(lines)
    
    def generate_combined_flow_diagram(
        self,
        analysis_data: Dict[str, Any]
    ) -> str:
        """
        Generate a comprehensive flow diagram from full analysis data.
        
        Args:
            analysis_data: Complete analysis output
            
        Returns:
            Mermaid syntax string
        """
        user_flows = analysis_data.get('user_flows', [])
        modules = analysis_data.get('modules', [])
        
        lines = ["flowchart TD"]
        lines.append("")
        
        # Add style classes
        lines.append("    classDef screenNode fill:#e0f2fe,stroke:#0284c7")
        lines.append("    classDef actionNode fill:#fef3c7,stroke:#f59e0b")
        lines.append("    classDef decisionNode fill:#fce7f3,stroke:#ec4899")
        lines.append("")
        
        # Start
        lines.append("    Start([Avvio Applicazione])")
        
        node_id = 0
        prev_node = "Start"
        
        # Add modules as main sections
        for mod_idx, module in enumerate(modules[:5]):  # Limit to 5 modules
            mod_name = module.get('name', f'Modulo {mod_idx + 1}')
            mod_desc = module.get('description', '')[:50]
            
            node_id += 1
            mod_node = f"M{node_id}"
            lines.append(f"    {mod_node}[{self._safe_mermaid_text(mod_name)}]")
            lines.append(f"    {prev_node} --> {mod_node}")
            prev_node = mod_node
        
        # Add user flows
        for flow_idx, flow in enumerate(user_flows[:3]):  # Limit to 3 flows
            flow_name = flow.get('name', f'Flusso {flow_idx + 1}')
            steps = flow.get('steps', [])
            
            if steps:
                node_id += 1
                flow_start = f"F{node_id}"
                lines.append(f"    {flow_start}[/{self._safe_mermaid_text(flow_name)}/]")
                lines.append(f"    {prev_node} --> {flow_start}")
                
                for step in steps[:5]:  # Limit steps per flow
                    action = step.get('action', '')[:40]
                    if action:
                        node_id += 1
                        step_node = f"S{node_id}"
                        lines.append(f"    {step_node}[{self._safe_mermaid_text(action)}]")
                        lines.append(f"    {flow_start} --> {step_node}")
        
        # End
        lines.append(f"    {prev_node} --> EndNode([Fine])")
        
        return "\n".join(lines)
    
    def generate_ascii_wireframe(
        self,
        frame_description: Dict[str, Any],
        width: int = 60,
        height: int = 30
    ) -> str:
        """
        Generate an ASCII wireframe representation from frame description.
        Uses specialized templates based on screen type.
        
        Args:
            frame_description: Parsed frame description with layout info
            width: Width of wireframe in characters
            height: Height of wireframe in lines
            
        Returns:
            ASCII wireframe string
        """
        logger.info("Generating ASCII wireframe")
        
        # Detect screen type
        screen_type = frame_description.get('screen_type', '').lower()
        layout = frame_description.get('layout', {})
        layout_type = layout.get('type', '').lower() if layout else ''
        
        # Combined type detection
        combined_type = f"{screen_type} {layout_type}"
        
        # Select template based on screen type
        if any(t in combined_type for t in ['modal', 'dialog', 'popup', 'overlay']):
            return self._wireframe_modal(frame_description, width, height)
        elif any(t in combined_type for t in ['form', 'input', 'editor']):
            return self._wireframe_form(frame_description, width, height)
        elif any(t in combined_type for t in ['table', 'list', 'grid', 'data']):
            return self._wireframe_table(frame_description, width, height)
        elif any(t in combined_type for t in ['dashboard', 'overview', 'home']):
            return self._wireframe_dashboard(frame_description, width, height)
        elif any(t in combined_type for t in ['navigation', 'menu', 'sidebar']):
            return self._wireframe_navigation(frame_description, width, height)
        else:
            return self._wireframe_generic(frame_description, width, height)
    
    def _wireframe_modal(self, desc: Dict[str, Any], width: int, height: int) -> str:
        """Generate modal/dialog wireframe."""
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        # Outer dimmed area
        for y in range(height):
            for x in range(width):
                grid[y][x] = '░'
        
        # Modal box (centered)
        modal_w = min(width - 10, 45)
        modal_h = min(height - 8, 18)
        start_x = (width - modal_w) // 2
        start_y = (height - modal_h) // 2
        
        # Clear modal area
        for y in range(start_y, start_y + modal_h):
            for x in range(start_x, start_x + modal_w):
                grid[y][x] = ' '
        
        # Modal border
        self._draw_box(grid, start_x, start_y, start_x + modal_w - 1, start_y + modal_h - 1)
        
        # Title bar
        self._draw_text(grid, start_x + 2, start_y + 1, "╔" + "═" * (modal_w - 6) + "╗")
        title = desc.get('layout', {}).get('header', 'Modal Dialog')
        self._draw_text(grid, start_x + 3, start_y + 2, self._truncate(title, modal_w - 8))
        self._draw_text(grid, start_x + modal_w - 4, start_y + 2, "[X]")
        
        # Content
        ocr = desc.get('ocr_extracted_texts', {})
        labels = ocr.get('labels', [])[:4]
        content_y = start_y + 5
        
        for i, label in enumerate(labels):
            if content_y + i * 2 < start_y + modal_h - 4:
                self._draw_text(grid, start_x + 3, content_y + i * 2, f"{self._truncate(label, 15)}:")
                self._draw_text(grid, start_x + 20, content_y + i * 2, "[___________]")
        
        # Buttons
        buttons = ocr.get('buttons', ['Conferma', 'Annulla'])[:2]
        btn_y = start_y + modal_h - 3
        btn_x = start_x + 5
        for btn in buttons:
            btn_text = f"[{self._truncate(btn, 10)}]"
            self._draw_text(grid, btn_x, btn_y, btn_text)
            btn_x += len(btn_text) + 3
        
        return '\n'.join([''.join(row) for row in grid])
    
    def _wireframe_form(self, desc: Dict[str, Any], width: int, height: int) -> str:
        """Generate form/input wireframe."""
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        self._draw_box(grid, 0, 0, width - 1, height - 1)
        
        # Header
        self._draw_text(grid, 2, 1, "╔" + "═" * (width - 6) + "╗")
        header = desc.get('layout', {}).get('header', 'Form')
        self._draw_text(grid, 4, 2, self._truncate(header, width - 10))
        self._draw_text(grid, 2, 3, "╚" + "═" * (width - 6) + "╝")
        
        # Form fields
        ocr = desc.get('ocr_extracted_texts', {})
        labels = ocr.get('labels', ['Nome', 'Email', 'Telefono', 'Indirizzo', 'Note'])[:6]
        
        form_y = 5
        for i, label in enumerate(labels):
            y = form_y + i * 3
            if y < height - 5:
                self._draw_text(grid, 3, y, f"{self._truncate(label, 18)}:")
                self._draw_box(grid, 3, y + 1, width - 4, y + 2)
        
        # Submit button
        buttons = ocr.get('buttons', ['Salva'])[:2]
        btn_y = height - 3
        btn_x = width - 20
        for btn in buttons:
            btn_text = f"[ {self._truncate(btn, 12)} ]"
            self._draw_text(grid, btn_x, btn_y, btn_text)
            btn_x -= len(btn_text) + 2
        
        return '\n'.join([''.join(row) for row in grid])
    
    def _wireframe_table(self, desc: Dict[str, Any], width: int, height: int) -> str:
        """Generate table/list wireframe."""
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        self._draw_box(grid, 0, 0, width - 1, height - 1)
        
        # Header
        header = desc.get('layout', {}).get('header', 'Lista Dati')
        self._draw_text(grid, 2, 1, f"▐ {self._truncate(header, width - 10)} ▌")
        
        # Toolbar
        self._draw_text(grid, 2, 3, "[+ Nuovo]  [✎ Modifica]  [🗑 Elimina]  [⟳ Aggiorna]")
        
        # Search bar
        self._draw_text(grid, 2, 5, "Cerca: [____________________________] [🔍]")
        
        # Table header
        table_y = 7
        col_widths = [(width - 6) // 4] * 4
        headers = ['ID', 'Nome', 'Stato', 'Data']
        
        self._draw_text(grid, 2, table_y, "┌" + "─" * (width - 5) + "┐")
        header_line = "│"
        for i, h in enumerate(headers):
            header_line += f" {h:^{col_widths[i]-2}} │"
        self._draw_text(grid, 2, table_y + 1, header_line[:width-3])
        self._draw_text(grid, 2, table_y + 2, "├" + "─" * (width - 5) + "┤")
        
        # Table rows
        for row in range(5):
            row_y = table_y + 3 + row
            if row_y < height - 4:
                row_line = "│"
                for i in range(4):
                    cell = "████" if i > 0 else f"{row+1:03d}"
                    row_line += f" {cell:^{col_widths[i]-2}} │"
                self._draw_text(grid, 2, row_y, row_line[:width-3])
        
        # Table footer
        self._draw_text(grid, 2, height - 4, "└" + "─" * (width - 5) + "┘")
        self._draw_text(grid, 2, height - 2, "Pagina 1 di 5  |  Mostra [10 ▼] elementi  |  Totale: 47")
        
        return '\n'.join([''.join(row) for row in grid])
    
    def _wireframe_dashboard(self, desc: Dict[str, Any], width: int, height: int) -> str:
        """Generate dashboard wireframe."""
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        self._draw_box(grid, 0, 0, width - 1, height - 1)
        
        # Header bar
        header = desc.get('layout', {}).get('header', 'Dashboard')
        self._draw_text(grid, 2, 1, f"☰  {self._truncate(header, 20)}  │  🔔 │ 👤")
        self._draw_text(grid, 2, 2, "─" * (width - 4))
        
        # Navigation tabs
        ocr = desc.get('ocr_extracted_texts', {})
        tabs = ocr.get('menu_items', ['Home', 'Vendite', 'Report', 'Impostazioni'])[:5]
        tab_x = 3
        for tab in tabs:
            tab_text = f"[{self._truncate(tab, 10)}]"
            self._draw_text(grid, tab_x, 3, tab_text)
            tab_x += len(tab_text) + 2
        
        # Stat cards row
        card_w = (width - 8) // 3
        cards = ['Totale', 'Oggi', 'Media']
        for i, card in enumerate(cards):
            card_x = 3 + i * (card_w + 2)
            self._draw_box(grid, card_x, 5, card_x + card_w - 1, 9)
            self._draw_text(grid, card_x + 2, 6, card)
            self._draw_text(grid, card_x + 2, 8, "█████")
        
        # Main content area
        content_w = (width - 8) * 2 // 3
        self._draw_box(grid, 3, 11, 3 + content_w, height - 4)
        self._draw_text(grid, 5, 12, "Grafico / Contenuto Principale")
        
        # Sidebar
        sidebar_x = 5 + content_w
        self._draw_box(grid, sidebar_x, 11, width - 3, height - 4)
        self._draw_text(grid, sidebar_x + 2, 12, "Attività Recenti")
        for i in range(4):
            if 14 + i < height - 5:
                self._draw_text(grid, sidebar_x + 2, 14 + i, f"• Elemento {i+1}")
        
        # Footer
        self._draw_text(grid, 3, height - 2, "© 2024  |  v1.0.0  |  Ultimo aggiornamento: ora")
        
        return '\n'.join([''.join(row) for row in grid])
    
    def _wireframe_navigation(self, desc: Dict[str, Any], width: int, height: int) -> str:
        """Generate navigation/menu wireframe."""
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        self._draw_box(grid, 0, 0, width - 1, height - 1)
        
        # Sidebar
        sidebar_w = 20
        self._draw_box(grid, 1, 1, sidebar_w, height - 2)
        
        # Logo
        self._draw_text(grid, 3, 2, "┌────────────┐")
        self._draw_text(grid, 3, 3, "│   LOGO     │")
        self._draw_text(grid, 3, 4, "└────────────┘")
        
        # Menu items
        ocr = desc.get('ocr_extracted_texts', {})
        menu = ocr.get('menu_items', ['Dashboard', 'Prodotti', 'Ordini', 'Clienti', 'Report', 'Impostazioni'])[:8]
        
        for i, item in enumerate(menu):
            y = 6 + i * 2
            if y < height - 4:
                prefix = "▸ " if i == 0 else "  "
                self._draw_text(grid, 3, y, f"{prefix}{self._truncate(item, 14)}")
        
        # Main content area
        self._draw_text(grid, sidebar_w + 4, 2, "Contenuto Principale")
        self._draw_text(grid, sidebar_w + 4, 3, "─" * (width - sidebar_w - 8))
        
        # Breadcrumb
        self._draw_text(grid, sidebar_w + 4, 5, "Home > Sezione > Pagina")
        
        # Content placeholder
        self._draw_box(grid, sidebar_w + 3, 7, width - 3, height - 4)
        self._draw_text(grid, sidebar_w + 6, 10, "Area contenuto selezionato")
        
        return '\n'.join([''.join(row) for row in grid])
    
    def _wireframe_generic(self, desc: Dict[str, Any], width: int, height: int) -> str:
        """Generate generic wireframe."""
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        self._draw_box(grid, 0, 0, width - 1, height - 1)
        
        layout = desc.get('layout', {})
        ocr = desc.get('ocr_extracted_texts', {})
        
        # Header
        self._draw_box(grid, 1, 1, width - 2, 4)
        header = layout.get('header', desc.get('summary', 'Schermata')[:30])
        self._draw_text(grid, 3, 2, f"☰  {self._truncate(header, width - 12)}")
        
        # Navigation tabs
        tabs = ocr.get('menu_items', [])[:4]
        if tabs:
            tab_x = 2
            for tab in tabs:
                tab_text = f"[{self._truncate(tab, 10)}]"
                self._draw_text(grid, tab_x, 5, tab_text)
                tab_x += len(tab_text) + 1
        
        # Main content
        content_y = 7
        summary = desc.get('summary', '')
        if summary:
            # Word wrap summary
            words = summary.split()
            line = ""
            for word in words[:30]:
                if len(line) + len(word) + 1 < width - 8:
                    line += word + " "
                else:
                    if content_y < height - 6:
                        self._draw_text(grid, 4, content_y, line.strip())
                        content_y += 1
                        line = word + " "
            if line and content_y < height - 6:
                self._draw_text(grid, 4, content_y, line.strip())
        
        # Buttons
        buttons = ocr.get('buttons', [])[:4]
        if buttons:
            btn_y = height - 4
            btn_x = 4
            for btn in buttons:
                btn_text = f"[{self._truncate(btn, 12)}]"
                self._draw_text(grid, btn_x, btn_y, btn_text)
                btn_x += len(btn_text) + 2
        
        # Footer
        self._draw_box(grid, 1, height - 3, width - 2, height - 2)
        self._draw_text(grid, 3, height - 2, "Status Bar")
        
        return '\n'.join([''.join(row) for row in grid])
    
    def _draw_box(self, grid: List[List[str]], x1: int, y1: int, x2: int, y2: int):
        """Draw a box on the grid."""
        height = len(grid)
        width = len(grid[0]) if grid else 0
        
        # Ensure bounds
        x1, x2 = max(0, x1), min(width - 1, x2)
        y1, y2 = max(0, y1), min(height - 1, y2)
        
        # Corners
        grid[y1][x1] = '+'
        grid[y1][x2] = '+'
        grid[y2][x1] = '+'
        grid[y2][x2] = '+'
        
        # Horizontal lines
        for x in range(x1 + 1, x2):
            grid[y1][x] = '-'
            grid[y2][x] = '-'
        
        # Vertical lines
        for y in range(y1 + 1, y2):
            grid[y][x1] = '|'
            grid[y][x2] = '|'
    
    def _draw_text(self, grid: List[List[str]], x: int, y: int, text: str):
        """Draw text on the grid."""
        if y < 0 or y >= len(grid):
            return
        
        width = len(grid[0]) if grid else 0
        for i, char in enumerate(text):
            if x + i >= width - 1:
                break
            if x + i >= 0:
                grid[y][x + i] = char
    
    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text to max length."""
        if not text:
            return ""
        text = str(text).replace('\n', ' ').strip()
        if len(text) <= max_len:
            return text
        return text[:max_len - 3] + "..."
    
    def _extract_app_name(self, text: str, max_length: int = 25) -> str:
        """
        Extract a clean, short app name from text that may be a full context or filename.
        
        Args:
            text: Input text (could be filename, context, or app name)
            max_length: Maximum length for the result
            
        Returns:
            Clean, short app name suitable for diagram labels
        """
        if not text:
            return "App"
        
        text = str(text).strip()
        
        # If it looks like a filename, extract just the name part
        if '.' in text and text.split('.')[-1].lower() in ['mp4', 'mov', 'avi', 'mkv', 'webm']:
            text = text.rsplit('.', 1)[0]
        
        # Try to extract app name from common patterns
        # Pattern: "App Name - Module" or "App_Name_Module"
        for separator in [' - ', ' _ ', '_', '-']:
            if separator in text:
                text = text.split(separator)[0].strip()
                break
        
        # If text is too long (likely a description/context), try to extract app name
        if len(text) > max_length:
            # Look for quoted app name like 'AppName' or "AppName"
            quoted_match = re.search(r"['\"]([^'\"]+)['\"]", text)
            if quoted_match:
                text = quoted_match.group(1)
            else:
                # Just take first few words
                words = text.split()[:3]
                text = ' '.join(words)
        
        # Final cleanup and truncation
        text = self._safe_mermaid_text(text)
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text if text else "App"
    
    def _safe_mermaid_text(self, text: str) -> str:
        """Make text safe for Mermaid diagrams."""
        if not text:
            return "N/A"
        # Remove or replace problematic characters
        text = str(text).replace('"', "'")
        text = text.replace('\n', ' ')
        text = text.replace('[', '(')
        text = text.replace(']', ')')
        text = text.replace('{', '(')
        text = text.replace('}', ')')
        text = text.replace('<', '')
        text = text.replace('>', '')
        text = text.replace('#', '')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()[:60]  # Limit length
    
    def render_mermaid_to_image_sync(
        self,
        mermaid_code: str,
        output_format: str = "png"
    ) -> Optional[bytes]:
        """
        Render Mermaid diagram to image using Kroki.io API (synchronous version).
        
        Args:
            mermaid_code: Mermaid syntax string
            output_format: Output format (png, svg, pdf)
            
        Returns:
            Image bytes or None if failed
        """
        import requests
        
        try:
            import base64
            import zlib
            
            # Encode for Kroki
            compressed = zlib.compress(mermaid_code.encode('utf-8'), 9)
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
            
            url = f"{self.kroki_url}/mermaid/{output_format}/{encoded}"
            
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                logger.info(f"Successfully rendered Mermaid diagram ({len(response.content)} bytes)")
                return response.content
            else:
                logger.error(f"Kroki API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to render Mermaid diagram: {e}")
            return None
    
    async def render_mermaid_to_png(
        self,
        mermaid_code: str,
        output_format: str = "png"
    ) -> Optional[bytes]:
        """
        Render Mermaid diagram to image using Kroki.io API (async version).
        
        Args:
            mermaid_code: Mermaid syntax string
            output_format: Output format (png, svg, pdf)
            
        Returns:
            Image bytes or None if failed
        """
        try:
            import base64
            import zlib
            
            # Encode for Kroki
            compressed = zlib.compress(mermaid_code.encode('utf-8'), 9)
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
            
            url = f"{self.kroki_url}/mermaid/{output_format}/{encoded}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Kroki API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to render Mermaid diagram: {e}")
            return None
    
    def get_mermaid_live_url(self, mermaid_code: str) -> str:
        """
        Generate a Mermaid Live Editor URL for the diagram.
        
        Args:
            mermaid_code: Mermaid syntax string
            
        Returns:
            URL to Mermaid Live Editor
        """
        import base64
        import json as json_module
        
        try:
            # Create state object for Mermaid Live
            state = {
                "code": mermaid_code,
                "mermaid": {"theme": "default"},
                "autoSync": True,
                "updateDiagram": True
            }
            
            # Encode state
            state_json = json_module.dumps(state)
            encoded = base64.urlsafe_b64encode(state_json.encode()).decode()
            
            return f"https://mermaid.live/edit#pako:{encoded}"
        except:
            # Fallback: simple base64 encoding
            encoded = base64.urlsafe_b64encode(mermaid_code.encode()).decode()
            return f"https://mermaid.live/edit#{encoded}"


def generate_all_diagrams(
    analysis_data: Dict[str, Any],
    keyframes_data: List[Dict[str, Any]],
    app_name: str = "App"
) -> Dict[str, str]:
    """
    Generate all diagram types from analysis data.
    
    Args:
        analysis_data: Full analysis output
        keyframes_data: List of keyframe descriptions
        app_name: Application name
        
    Returns:
        Dictionary with diagram types as keys and Mermaid/ASCII as values
    """
    generator = DiagramGenerator()
    
    result = {}
    
    # Sequence diagram
    user_flows = analysis_data.get('user_flows', [])
    if user_flows:
        result['sequence_diagram'] = generator.generate_sequence_diagram(
            user_flows,
            app_name=app_name
        )
    
    # User flow diagram
    if user_flows or analysis_data.get('modules'):
        result['user_flow_diagram'] = generator.generate_user_flow_diagram(
            user_flows,
            analysis_data.get('modules', [])
        )
    
    # Combined flow
    result['combined_flow'] = generator.generate_combined_flow_diagram(analysis_data)
    
    # Wireframes for each keyframe
    wireframes = []
    for idx, kf in enumerate(keyframes_data[:5]):  # Limit to 5 wireframes
        desc = kf.get('description', '')
        if desc:
            try:
                desc_data = json.loads(desc) if isinstance(desc, str) else desc
                wireframe = generator.generate_ascii_wireframe(desc_data)
                wireframes.append({
                    'timestamp': kf.get('timestamp', 0),
                    'wireframe': wireframe
                })
            except:
                pass
    
    result['wireframes'] = wireframes
    
    return result


if __name__ == "__main__":
    # Test diagram generation
    print("DiagramGenerator module loaded successfully.")
    
    # Test with sample data
    test_flows = [
        {
            "name": "Aggiunta Tavolo",
            "steps": [
                {"action": "Clicca su Modifica Sale", "timestamp": "0:10"},
                {"action": "Seleziona + per aggiungere", "timestamp": "0:15"},
                {"action": "Sceglie forma tavolo", "timestamp": "0:20"},
                {"action": "Inserisce nome tavolo", "timestamp": "0:25"},
                {"action": "Conferma", "timestamp": "0:30", "outcome": "Tavolo creato"}
            ]
        }
    ]
    
    gen = DiagramGenerator()
    seq = gen.generate_sequence_diagram(test_flows, app_name="Tilby")
    print("\n=== Sequence Diagram ===")
    print(seq)
    
    flow = gen.generate_user_flow_diagram(test_flows)
    print("\n=== User Flow Diagram ===")
    print(flow)

