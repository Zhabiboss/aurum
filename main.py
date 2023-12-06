import os
import sys
import pygame
from settings import *
import json
import tkinter
import colorama
from colorama import Fore, Back, Style

colorama.init(autoreset = True)

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
                      "bold+italic": pygame.font.SysFont("Consolas", 16, True, True),
                      "normal_small": pygame.font.SysFont("Consolas", 4),
                      "bold_small": pygame.font.SysFont("Consolas", 4, True),
                      "italic_small": pygame.font.SysFont("Consolas", 4, False, True),
                      "bold+italic_small": pygame.font.SysFont("Consolas", 4, True, True)}
    
    def parseLine(self, line: str) -> list[tuple[str, str]]:
        words = line.split(" ")
        parsed_line = []
        for word in words:
            if word.startswith(""):
                parsed_line.append((word[10:], "bold"))
            elif word.startswith(""):
                parsed_line.append((word[10:], "italic"))
            elif word.startswith(""):
                parsed_line.append((word[10:], "italic+bold"))
            elif word.startswith(""):
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

    def renderSmallLine(self, pos: tuple[int, int], line: list[tuple[str, str]]):
        prev_len = 0
        for idx, (element, style) in enumerate(line):
            font = self.fonts[style + "_small"]
            text = font.render(element.replace("\t", "    "), True, self.editor.textColor)
            self.editor.screen.blit(text, (pos[0] + prev_len, pos[1]))
            prev_len += text.get_width() + font.render(" ", True, "white").get_width()
    
    def drawContent(self, content: list[list[tuple[str, str]]], horizontalOffset: int, vertical_offset: int, start_pos: tuple[int, int] = (0, 0)):
        y_offset = self.fonts["normal"].render("W", True, "white").get_height() + 2
        x_offset = self.fonts["normal"].render("W", True, "white").get_width()
        line_number_width = max(30, len(str(len(content))) * 10)

        for idx, line in enumerate(content):
            line_number_text = self.fonts["normal"].render(str(idx + 1), True, self.editor.textColor)
            self.editor.screen.blit(line_number_text, (start_pos[0] - horizontalOffset * x_offset, start_pos[1] + y_offset * idx - vertical_offset * y_offset))

            text_start_pos = (start_pos[0] + line_number_width - horizontalOffset * x_offset, start_pos[1] + y_offset * idx - vertical_offset * y_offset)
            self.renderLine(text_start_pos, line)
        pygame.draw.line(self.editor.screen, self.editor.outlineColor, (start_pos[0] + line_number_width - horizontalOffset * x_offset, start_pos[1]), (start_pos[0] + line_number_width, HEIGHT))

    def drawCursor(self):
        # Calculate the actual cursor position considering tabs
        line_number_width = max(30, len(str(len(self.editor.content))) * 10)
        contentBeforeCursor = self.editor.content[:self.editor.cursorPosition]
        expandedBeforeCursor = contentBeforeCursor.replace("\t", "    ")  # Replace tabs with spaces
        cursorLineIndex = expandedBeforeCursor.count('\n') - self.editor.verticalOffset
        charInLineAmount = len(expandedBeforeCursor.split('\n')[-1])

        y_offset = self.fonts["normal"].render("W", True, "white").get_height() + 2
        y = OFFSET[1] + (cursorLineIndex + 1) * y_offset
        x = OFFSET[0] + charInLineAmount * (self.fonts["normal"].render("W", True, "white").get_width()) + line_number_width

        if y >= OFFSET[1] and y < HEIGHT - OFFSET[1]:  # Draw cursor only if it's within the visible area
            pygame.draw.line(self.editor.screen, self.editor.cursorColor, (x, y), (x, y - self.fonts["normal"].render("W", True, "white").get_height()))

    def drawBackground(self):
        c1, c2 = self.editor.backgroundColor1, self.editor.backgroundColor2
        surf = pygame.Surface((2, 2))
        pygame.draw.line(surf, c1, (0, 0), (1, 0))
        pygame.draw.line(surf, c2, (0, 1), (1, 1))
        rect = pygame.transform.smoothscale(surf, (WIDTH, HEIGHT))
        self.editor.screen.blit(rect, (0, 0))

    def drawSmallCodeWindow(self, horizonalOffset: int, vertical_offset: int):
        start_pos = OFFSET[0], OFFSET[1]
        y_offset = self.fonts["normal_small"].render("W", True, "white").get_height() + 2
        x_offset = self.fonts["normal_small"].render("W", True, "white").get_width()
        line_number_width = max(30, len(str(len(self.editor.content))) * 10)

        for idx, line in enumerate(self.editor.styleHandler.parseContent(self.editor.content)):
            #line_number_text = self.fonts["normal_small"].render(str(idx + 1), True, self.editor.textColor)
            #self.editor.screen.blit(line_number_text, (start_pos[0], start_pos[1] + y_offset * idx))

            text_start_pos = (start_pos[0] + line_number_width - horizonalOffset * x_offset, start_pos[1] + y_offset * idx - vertical_offset * y_offset)
            self.renderSmallLine(text_start_pos, line)


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
                if word.startswith("#"):
                    parsed_line.append((word, "bold"))
                else:
                    parsed_line.append((word, "normal"))
            parsed_lines.append(parsed_line)
        return parsed_lines
    
    def removeMarkup(self, content: str) -> str:
        content = content.replace("", "")
        content = content.replace("", "")
        content = content.replace("", "")
        content = content.replace("", "")
        return content
    
    def loadTheme(self, themepath: str = "themes/1.json") -> tuple[str, str, str, str, str]:
        theme: dict = json.load(open(themepath, "r"))
        textColor = theme["textColor"]
        backgroundColor1 = theme["backgroundColor1"]
        backgroundColor2 = theme["backgroundColor2"]
        cursorColor = theme["cursorColor"]
        outlineColor = theme["outlineColor"]
        return textColor, backgroundColor1, backgroundColor2, cursorColor, outlineColor

class Editor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            print("Error: no such file")
            sys.exit(1)
        with open(filepath, "r") as file:
            self.content = file.read()
            file.close()
        self.file = open(self.filepath, "w")
        self.deltaTime = 1 / FPS
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode(RESOLUTION)
        pygame.display.set_caption(f"Aurum - {self.filepath}")
        self.styleHandler = StyleHandler(self)
        self.currentTheme = json.load(open("themes/current.json", "r"))["current_theme"]
        theme = self.styleHandler.loadTheme(self.currentTheme)
        self.textColor = theme[0]
        self.backgroundColor1 = theme[1]
        self.backgroundColor2 = theme[2]
        self.cursorColor = theme[3]
        self.outlineColor = theme[4]
        self.keyHandler = KeyHandler(self)
        self.graphicsHandler = GraphicsHandler(self)
        self.isUppercase = False
        self.isKeyBind = False
        self.nonCharKeys = ["\t", "left shift", "right shift", "left ctrl", "right ctrl", "space", "caps lock", "left alt", "right alt", "numlock", "delete", "end", "home", "insert", "page up", "page down", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "escape", "up", "down", "right", "left", "print screen", "scroll lock"]
        self.uppercaseReplacement = {"1": "!", "2": "@", "3": "#", "4": "$", "5": "%", "6": "^", "7": "&", "8": "*", "9": "(", "0": ")", "-": "_", "=" :"+", "`": "~", "'": "\"", ",": "<", ".": ">", "/": "?", ";": ":"}
        self.cursorPosition = len(self.content)
        self.verticalOffset = 0
        self.horizontalOffset = 0
        self.linesPerPage = HEIGHT // (self.graphicsHandler.fonts["normal"].get_height() + 2)
        self.autoSaveInterval = len(self.styleHandler.removeMarkup(self.content)) / 1000
        self.timeSinceLastSave = 0
        self.saveFile()
        self.undoStack = []
        self.redoStack = []
        self.saveState()  # Save the initial state

    def saveState(self):
        self.undoStack.append((self.content, self.cursorPosition))

    def undo(self):
        if self.undoStack:
            self.redoStack.append((self.content, self.cursorPosition))
            self.content, self.cursorPosition = self.undoStack.pop()

    def redo(self):
        if self.redoStack:
            self.undoStack.append((self.content, self.cursorPosition))
            self.content, self.cursorPosition = self.redoStack.pop()

    def saveFile(self):
        content = self.styleHandler.removeMarkup(self.content)
        with open(self.filepath, "w") as file:
            file.write(content)
            file.close()

    def getClipboardContent(self) -> str:
        root = tkinter.Tk()
        pastedText = root.clipboard_get()
        root.destroy()
        return pastedText
    
    def setClipboardContent(self, content: str):
        root = tkinter.Tk()
        root.clipboard_append(content)
        root.destroy()

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
                        if self.horizontalOffset != 0:
                            self.horizontalOffset -= 1

                elif key_output in self.nonCharKeys:
                    # Handle special non-character keys here
                    if key_output == "\t":
                        self.saveState()
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
                        if self.horizontalOffset != 0:
                            self.horizontalOffset -= 1
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
                
                elif self.isKeyBind and key_output == "z":
                    self.undo()
                
                elif self.isKeyBind and key_output == "y":
                    self.redo()
                
                elif self.isKeyBind and key_output == "w":
                    pass

                elif self.isKeyBind and key_output == "v":
                    self.saveState()
                    pastedText = self.getClipboardContent()
                    self.content = self.content[:self.cursorPosition] + pastedText + self.content[self.cursorPosition:]
                    self.cursorPosition += len(pastedText)

                elif self.isKeyBind and key_output in "123456789":
                    if os.path.isfile(f"themes/{key_output}.json"):
                        self.currentTheme = f"themes/{key_output}.json"
                        self.textColor = self.styleHandler.loadTheme(self.currentTheme)[0]
                        self.backgroundColor1 = self.styleHandler.loadTheme(self.currentTheme)[1]
                        self.backgroundColor2 = self.styleHandler.loadTheme(self.currentTheme)[2]
                        self.cursorColor = self.styleHandler.loadTheme(self.currentTheme)[3]
                        self.outlineColor = self.styleHandler.loadTheme(self.currentTheme)[4]

                elif key_output is not None:
                    self.saveState()
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

        activeFPS = self.clock.get_fps()
        deltaTime = 1 / activeFPS if activeFPS != 0 else 1 / FPS
        self.timeSinceLastSave += deltaTime
        if self.timeSinceLastSave >= self.autoSaveInterval:
            self.timeSinceLastSave = 0
            self.saveFile()
            json.dump({"current_theme": self.currentTheme}, open("themes/current.json", "w"))

        if pygame.key.get_pressed()[pygame.K_PAGEUP]:
            beforeContent = self.content[:self.cursorPosition]
            if len(beforeContent.split("\n")) != 1:
                self.cursorPosition -= len(beforeContent.split("\n")[-1]) + 1
            else:
                self.cursorPosition = 0

        if pygame.key.get_pressed()[pygame.K_PAGEDOWN]:
            afterContent = self.content[self.cursorPosition:]
            if len(afterContent.split("\n")) != 1:
                self.cursorPosition += len(afterContent.split("\n")[0]) + 1
            else:
                self.cursorPosition = len(self.content)

        self.keyHandler.onUpdate()
        pygame.display.update()
        self.clock.tick(FPS)

    def draw(self):
        self.graphicsHandler.drawBackground()

        if self.isKeyBind and pygame.key.get_pressed()[pygame.K_w]:
            self.graphicsHandler.drawSmallCodeWindow(self.horizontalOffset, self.verticalOffset)
        else:
            # Calculate the current line of the cursor
            cursor_line = (self.content[:self.cursorPosition].count('\n') + 1)

            # Adjust vertical offset if the cursor is outside the visible range
            if cursor_line < self.verticalOffset:
                self.verticalOffset = max(cursor_line - 1, 0)
            elif cursor_line >= self.verticalOffset + self.linesPerPage:
                self.verticalOffset = cursor_line - self.linesPerPage
            
            cursor_x = len(self.content[:self.cursorPosition].split("\n")[-1])
            if (cursor_x + 2) * self.graphicsHandler.fonts["normal"].render("W", True, "white").get_width() + OFFSET[0] * 2 > WIDTH + self.horizontalOffset * self.graphicsHandler.fonts["normal"].render("W", True, "white").get_width():
                self.horizontalOffset += 1

            parsedContent = self.styleHandler.parseContent(self.content)
            for line in parsedContent:
                for word in line:
                    if word[0].startswith("!") and word[1] == "normal":
                        parsedContent[parsedContent.index(line)].remove(word)
            self.graphicsHandler.drawContent(parsedContent, self.horizontalOffset, self.verticalOffset, OFFSET)
            self.graphicsHandler.drawCursor()

    def run(self):
        while True:
            self.update()
            self.draw()

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        with open(sys.argv[1], "a") as file:
            print(f"Creating/opening file '{sys.argv[1]}'...")
            file.close()
        editor = Editor(sys.argv[1])
        backup = editor.styleHandler.removeMarkup(editor.content)
        try:
            editor.run()
        except:
            print(Fore.RED + "Unexpected error: writing file backup...")
            with open(sys.argv[1], "w") as file:
                file.write(backup)
                file.close()
            print(Fore.GREEN + "Rollback completed!")
            sys.exit(2)
    else:
        with open("untitled.txt", "a") as file:
            print(f"Creating/opening file 'untitled.txt'...")
            file.close()
        editor = Editor("untitled.txt")
        backup = editor.styleHandler.removeMarkup(editor.content)
        try:
            editor.run()
        except:
            print(Fore.RED + "Unexpected error: writing file backup...")
            with open("untitled.txt", "w") as file:
                file.write(backup)
                file.close()
            print(Fore.GREEN + "Rollback completed!")
            sys.exit(2)