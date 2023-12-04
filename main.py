import os
import sys
import pygame
from settings import *
import json

class KeyHandler:
    def __init__(self, editor):
        self.editor = editor
        
    def onUpdate(self):
        ...

    def toName(self, key: int) -> str:
        return pygame.key.name(key)
    
    def handleKeys(self, event) -> str | None | int:
        if event.type == pygame.KEYDOWN:
            content = None
            if event.key == pygame.K_TAB:
                content = "\t"
            elif event.key == pygame.K_BACKSPACE:
                content = -1
            elif event.key == pygame.K_RETURN:
                content = "\n"
            elif event.key == pygame.K_SPACE:
                content = " "
            else:
                content = self.toName(event.key)
            return content
        else:
            return None
        
class GraphicsHandler:
    def __init__(self, editor):
        pygame.init()
        self.editor = editor
        self.fonts = {"normal": pygame.font.SysFont("Consolas", 16),
                      "bold": pygame.font.SysFont("Consolas", 16, True),
                      "italic": pygame.font.SysFont("Consolas", 16, False, True),
                      "bold+italic": pygame.font.SysFont("Consolas", 16, True, True)}
    
    def parseLine(self, line: str) -> list[tuple[str, str]]:
        words = line.split(" ")
        parsed_line = []
        for word in words:
            if word.startswith("[~|bold|~]"):
                parsed_line.append((word[10:], "bold"))
            elif word.startswith("[~|ital|~]"):
                parsed_line.append((word[10:], "italic"))
            elif word.startswith("[~|i+bol|~]"):
                parsed_line.append((word[10:], "italic+bold"))
            elif word.startswith("[~|norm|~]"):
                parsed_line.append((word[10:], "normal"))
            else:
                parsed_line.append((word, "normal"))

        return parsed_line
        
    def renderLine(self, pos: tuple[int, int], line: list[tuple[str, str]]):
        prev_len = 0
        for idx, (element, style) in enumerate(line):
            font = self.fonts[style]
            text = font.render(element.replace("\t", "    "), True, self.editor.textColor)
            self.editor.screen.blit(text, (pos[0] + prev_len, pos[1]))
            prev_len += text.get_width() + font.render(" ", True, "white").get_width()
    
    def drawContent(self, content: list[list[tuple[str, str]]], vertical_offset: int, start_pos: tuple[int, int] = (0, 0)):
        y_offset = self.fonts["normal"].render("W", True, "white").get_height() + 2
        line_number_width = max(30, len(str(len(content))) * 10)

        for idx, line in enumerate(content):
            line_number_text = self.fonts["normal"].render(str(idx + 1), True, self.editor.textColor)
            self.editor.screen.blit(line_number_text, (start_pos[0], start_pos[1] + y_offset * idx - vertical_offset * y_offset))

            text_start_pos = (start_pos[0] + line_number_width, start_pos[1] + y_offset * idx - vertical_offset * y_offset)
            self.renderLine(text_start_pos, line)
        pygame.draw.line(self.editor.screen, self.editor.outlineColor, (start_pos[0] + line_number_width, start_pos[1]), (start_pos[0] + line_number_width, HEIGHT))

    def drawCursor(self):
        content = self.editor.content.replace("\t", "    ")
        tabs = self.editor.content[:self.editor.cursorPosition].count("\t")
        contentBeforeCursor = content[:self.editor.cursorPosition + tabs * 4]
        cursorLineIndex = contentBeforeCursor.count('\n') - self.editor.verticalOffset
        charInLineAmount = len(contentBeforeCursor.split('\n')[-1])
        
        y_offset = self.fonts["normal"].render("W", True, "white").get_height() + 2
        y = OFFSET[1] + (cursorLineIndex + 1) * y_offset
        x = OFFSET[0] + (charInLineAmount + 3) * (self.fonts["normal"].render("W", True, "white").get_width())

        if y >= OFFSET[1] and y < HEIGHT - OFFSET[1]:  # Draw cursor only if it's within the visible area
            pygame.draw.line(self.editor.screen, self.editor.cursorColor, (x, y), (x, y - self.fonts["normal"].render("W", True, "white").get_height()))


class StyleHandler:
    def __init__(self, editor):
        self.editor = editor

    def parseContent(self, content: str) -> list[list[tuple[str, str]]]:
        lines = content.split("\n")
        parsed_lines = []
        for line in lines:
            words = line.split(" ")
            parsed_line = []
            for word in words:
                if word.startswith("!"):
                    parsed_line.append((word, "italic"))
                else:
                    parsed_line.append((word, "normal"))
            parsed_lines.append(parsed_line)
        return parsed_lines
    
    def removeMarkup(self, content: str) -> str:
        content = content.replace("[~|norm|~]", "")
        content = content.replace("[~|ital|~]", "")
        content = content.replace("[~|bold|~]", "")
        content = content.replace("[~|i+bol|~]", "")
        return content
    
    def loadTheme(self) -> tuple[str, str, str, str]:
        theme: dict = json.load(open("themes/current.json", "r"))
        textColor = theme["textColor"]
        backgroundColor = theme["backgroundColor"]
        cursorColor = theme["cursorColor"]
        outlineColor = theme["outlineColor"]
        return textColor, backgroundColor, cursorColor, outlineColor

class Editor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            print("Error: no such file")
            sys.exit(1)
        with open(self.filepath, "r") as file:
            self.content = file.read()
            file.close()
        self.file = open(self.filepath, "w")
        self.deltaTime = 1 / FPS
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode(RESOLUTION)
        pygame.display.set_caption(f"Aurum - {self.filepath}")
        self.styleHandler = StyleHandler(self)
        self.textColor = self.styleHandler.loadTheme()[0]
        self.backgroundColor = self.styleHandler.loadTheme()[1]
        self.cursorColor = self.styleHandler.loadTheme()[2]
        self.outlineColor = self.styleHandler.loadTheme()[3]
        self.keyHandler = KeyHandler(self)
        self.graphicsHandler = GraphicsHandler(self)
        self.isUppercase = False
        self.isKeyBind = False
        self.nonCharKeys = ["\t", "left shift", "right shift", "left ctrl", "right ctrl", "space", "caps lock", "left alt", "right alt", "numlock", "delete", "end", "home", "insert", "page up", "page down", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "escape", "up", "down", "right", "left", "print screen", "scroll lock"]
        self.uppercaseReplacement = {"1": "!", "2": "@", "3": "#", "4": "$", "5": "%", "6": "^", "7": "&", "8": "*", "9": "(", "0": ")", "-": "_", "=" :"+", "`": "~", "'": "\"", ",": "<", ".": ">", "/": "?", ";": ":"}
        self.cursorPosition = len(self.content)
        self.verticalOffset = 0
        self.linesPerPage = HEIGHT // (self.graphicsHandler.fonts["normal"].get_height() + 2)

    def saveFile(self):
        content = self.styleHandler.removeMarkup(self.content)
        self.file.write(content)
        self.file.close()
        sys.exit(0)

    def update(self):
        if self.content == "":
            self.cursorPosition = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            
            if event.type == pygame.KEYDOWN:
                key_output = self.keyHandler.handleKeys(event)

                if key_output == -1:  # Backspace
                    if self.cursorPosition != 0:
                        self.content = self.content[:self.cursorPosition - 1] + self.content[self.cursorPosition:]
                        self.cursorPosition -= 1

                elif key_output in self.nonCharKeys:
                    # Handle special non-character keys here
                    if key_output == "\t":
                        self.content = self.content[:self.cursorPosition] + key_output + self.content[self.cursorPosition:]
                        self.cursorPosition += 1
                    if key_output == "left shift":
                        self.isUppercase = True
                    elif key_output == "left ctrl":
                        self.isKeyBind = True
                    elif key_output == "right":
                        if self.cursorPosition < len(self.content):
                            self.cursorPosition += 1
                    elif key_output == "left":
                        if self.cursorPosition > 0:
                            self.cursorPosition -= 1
                    elif key_output == "up":
                        beforeContent = self.content[:self.cursorPosition]
                        if len(beforeContent.split("\n")) != 1:
                            self.cursorPosition -= len(beforeContent.split("\n")[-1]) + 1
                        else:
                            self.cursorPosition = 0
                    elif key_output == "down":
                        afterContent = self.content[self.cursorPosition:]
                        if len(afterContent.split("\n")) != 1:
                            self.cursorPosition += len(afterContent.split("\n")[0]) + 1
                        else:
                            self.cursorPosition = len(self.content)
                
                elif self.isKeyBind and key_output == "s":
                    self.saveFile()

                elif key_output is not None:
                    # Insert character at cursor position
                    if self.isUppercase and key_output in self.uppercaseReplacement.keys():
                        key_output = self.uppercaseReplacement[key_output]
                    elif self.isUppercase:
                        key_output = key_output.upper()

                    self.content = self.content[:self.cursorPosition] + key_output + self.content[self.cursorPosition:]
                    self.cursorPosition += 1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LSHIFT:
                    self.isUppercase = False
                if event.key == pygame.K_LCTRL:
                    self.isKeyBind = False

        self.keyHandler.onUpdate()
        pygame.display.update()

    def draw(self):
        self.screen.fill(self.backgroundColor)

        # Calculate the current line of the cursor
        cursor_line = (self.content[:self.cursorPosition].count('\n') + 1)

        # Adjust vertical offset if the cursor is outside the visible range
        if cursor_line < self.verticalOffset:
            self.verticalOffset = max(cursor_line - 1, 0)
        elif cursor_line >= self.verticalOffset + self.linesPerPage:
            self.verticalOffset = cursor_line - self.linesPerPage

        self.graphicsHandler.drawContent(self.styleHandler.parseContent(self.content), self.verticalOffset, OFFSET)
        self.graphicsHandler.drawCursor()

    def run(self):
        while True:
            self.update()
            self.draw()

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        with open(sys.argv[1], "w") as file:
            print(f"Creating/opening file '{sys.argv[1]}'...")
            file.close()
        editor = Editor(sys.argv[1])
        editor.run()
    else:
        with open("untitled.txt", "w") as file:
            print(f"Creating/opening file 'untitled.txt'...")
            file.close()
        editor = Editor("untitled.txt")
        editor.run()