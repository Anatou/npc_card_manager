import pygame
from random import randint
from math import ceil
from easygui import filesavebox, fileopenbox
from json import loads, dumps


# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #
#           GLOBAL VARIABLES              #
# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #
pygame.init()
pygame.font.init()
pygame.key.set_repeat(400, 30) #Active la possibilité de rester appuyer sur une touche


WIDTH, HEIGHT = 1440, 810

#Initialisation de la fenêtre pygame
pygame.display.set_caption("NPC card manager prototype")
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE | pygame.DOUBLEBUF)

mb1_down, mb2_down, mb3_down = False, False, False
dragged_card = -1
drag_offset = [0,0]

object_edited = ""
card_edited = -1
deck_edited = -1

show_debug_info = False
debug_info_x_pos = WIDTH-70

deck_menu_opened = -1
was_deck_menu_opened = False
deck_offset = [0,0,0,0,0,0]

render_copy_context_menu = False

is_shift_pressed = False

# font setup
arial = pygame.font.SysFont('Arial', 20)
arial_15 = pygame.font.SysFont('Arial', 15)

# max fps initialization
maxFPS = 60
deltaTime = maxFPS/1000
pygame_clock = pygame.time.Clock()

# list of all the cards out of the deck
cards = list()


color_atlas = {
    "default": {
        "bg_color":(255,255,255),
        "border_color":(200,200,200),
    },
    "pc": {
        "bg_color":(100,255,100),
        "border_color":(0,200,0),
    },
    "npc": {
        "bg_color":(255,255,100),
        "border_color":(200,200,0),
    },
    "mtr": {
        "bg_color":(255,100,150),
        "border_color":(200,0,50),
    },
    "bss": {
        "bg_color":(200,0,0),
        "border_color":(255,0,0),
    },
    "min": {
        "bg_color":(255,200,255),
        "border_color":(255,150,225),
    },
}

# textures at native high resolution in case of a scale up or zoom in
raw_texture_atlas = {
    "deck_0":pygame.image.load("./textures/deck_0.png").convert_alpha(),
    "deck_1":pygame.image.load("./textures/deck_1.png").convert_alpha(),
    "deck_2":pygame.image.load("./textures/deck_2.png").convert_alpha(),
    "deck_3":pygame.image.load("./textures/deck_3.png").convert_alpha(),

    "default_card":pygame.image.load("./textures/default_card.png").convert_alpha(),
    "npc_card":pygame.image.load("./textures/npc_card.png").convert_alpha(),
    "pc_card":pygame.image.load("./textures/pc_card.png").convert_alpha(),
    "mtr_card":pygame.image.load("./textures/mtr_card.png").convert_alpha(),
    "bss_card":pygame.image.load("./textures/bss_card.png").convert_alpha(),

}

# manually changed with up and down arrows
scale = 1


update_display = True




# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #
#                FUNCTIONS                #
# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #

def draw_rect_alpha(surface, color, rect):
    shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
    pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
    surface.blit(shape_surf, rect)

def load_deck(pos_number):
    path = fileopenbox(default="*/*.deck", filetypes="*.deck")
    if not path: return None
    with open(path, "r") as file:
        data = loads(file.read())
    deck = Deck(data["title"], pos_number)
    for card in data["cards"]:
        deck.cards.append(Card(card["name"], card["type"], card["ca"], card["mvt"], card["p_perception"], card["hp"], card["attributes"], card["txt"], card["size"], card["pos"], pygame.image.fromstring(bytes.fromhex(card["image"]), card["image_size"], "RGBA")))
    global update_display
    update_display = True
    return deck

def resize_textures():
    resized_textures = dict()
    for key, item in raw_texture_atlas.items():
        item_size = item.get_size()
        resized_textures[key] = pygame.transform.smoothscale(item, (item_size[0]/3, item_size[1]/3))
    return resized_textures

# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #
#                 CLASSES                 #
# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #

class ColorAtlas:
    @staticmethod
    def bg_color(wanted_color):
        if wanted_color in color_atlas.keys():
            return color_atlas[wanted_color]["bg_color"]
        else:
            return color_atlas["default"]["bg_color"]

    @staticmethod
    def border_color(wanted_color):
        if wanted_color in color_atlas.keys():
            return color_atlas[wanted_color]["border_color"]
        else:
            return color_atlas["default"]["border_color"]


class TextField:
    def __init__(self, text="", pos=(10,10), max_width=1000, text_color=(0,0,0), font="Arial", font_size=30):
        self.text = str(text)
        self.pos = list(pos)
        self.max_width = max_width
        self.text_color = text_color
        self.font = font
        self.font_size = font_size
        self.is_edited = False

        font = pygame.font.SysFont(self.font, self.font_size)
        self.current_width = font.size(self.text)[0]

        self.cursor_timer = 0.5


    def set_text(self,text):
        font = pygame.font.SysFont(self.font, self.font_size)
        while font.size(text)[0] >= self.max_width:
            text = text[:-1]
        self.text = text
    
    def write(self, event):
        self.is_edited = True
        font = pygame.font.SysFont(self.font, self.font_size)
        if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE: #Si entrée ou escape appuyé
            self.is_edited = False
            return False
        elif event.key == pygame.K_BACKSPACE: #Si retour appuyé
            key_pressed = pygame.key.get_pressed()
            # si ctrl+supp
            if key_pressed[pygame.K_LCTRL] or key_pressed[pygame.K_RCTRL]:
                # supprimer le dernier mot
                space_index = 0
                for ii in range(len(self.text)-1, 0, -1):
                    if self.text[ii-1] == " ":
                        space_index = ii-1
                        break
                self.text = self.text[:space_index]
                self.cursor_timer = 0.5
            else:
            # si just supp
                self.text = self.text[:-1] #supprime dernier charactère
                self.cursor_timer = 0.5
        else: # si autre charactère est entré
            if font.size(self.text + event.unicode)[0] < self.max_width:
                self.text += event.unicode #ajouter le charactère associé à la touche appuyée au champ d'entrée
                self.cursor_timer = 0.5
            
        self.current_width = font.size(self.text)[0]
        return True

    def click(self):
        if pygame.mouse.get_pressed()[0] and not mb1_down:
            mouse_pos = pygame.mouse.get_pos()
            return mouse_pos[0] >= self.pos[0] and mouse_pos[0] <= self.pos[0]+self.max_width and mouse_pos[1] >= self.pos[1] and mouse_pos[1] <= self.pos[1]+self.font_size


    def render(self, offset=(0,0)):
        suffix = ""
        if self.is_edited:
            self.cursor_timer -= deltaTime*0.001
            if self.cursor_timer < -0.5:
                self.cursor_timer += 1
            elif self.cursor_timer < 0:
                suffix = ""
            else:
                suffix = "|"

        font = pygame.font.SysFont(self.font, self.font_size)
        text = font.render(self.text+suffix, True, self.text_color)
        screen.blit(text, (self.pos[0]+offset[0],self.pos[1]+offset[1]))


class Card:
    global screen
    def __init__(self, name="Name", type="npc", ca=10, mvt=18, p_perception=10, hp=15, attributes={"str":"10","dex":"10","con":"10","int":"10","wis":"10","cha":"10",}, txt=["", "", ""], size=(200,300), pos=(10,10), image=pygame.Surface((170,170))):

        self.name = name
        self.type = type
        self.ca = str(ca)
        self.mvt = str(mvt)
        self.p_perception = str(p_perception)
        self.hp = str(hp)
        self.attributes = attributes
        self.size = list(size)
        self.pos = list(pos)

        self.txt = txt

        self.image = image
        self.image_pos = (self.pos[0]+15, self.pos[1]+35)

        self.editing = ""
        self.text_fields = {
            "type":TextField(self.type, (0,0), 30, font_size=15), # check for "xxx_card" in the texture_altas for all possible variants
            "name":TextField(self.name, (self.pos[0]+45, self.pos[1]+13), self.size[0]-60, font_size=20),
            "ca":TextField(self.ca, (0,0), 20, font_size=15),
            "mvt":TextField(self.mvt, (0,0), 20, font_size=15),
            "p_perception":TextField(self.p_perception, (0,0), 20, font_size=15),
            "hp":TextField(self.hp, (0,0), 30, font_size=15),
            "str":TextField(attributes["str"], (0,0), 20, font_size=15),
            "dex":TextField(attributes["dex"], (0,0), 20, font_size=15),
            "con":TextField(attributes["con"], (0,0), 20, font_size=15),
            "int":TextField(attributes["int"], (0,0), 20, font_size=15),
            "wis":TextField(attributes["wis"], (0,0), 20, font_size=15),
            "cha":TextField(attributes["cha"], (0,0), 20, font_size=15),

            "txt1":TextField(txt[0], (self.pos[0]+20,self.pos[1]+self.size[1]-68), self.size[0]-37, font_size=15),
            "txt2":TextField(txt[1], (self.pos[0]+20,self.pos[1]+self.size[1]-50), self.size[0]-37, font_size=15),
            "txt3":TextField(txt[2], (self.pos[0]+20,self.pos[1]+self.size[1]-32), self.size[0]-37, font_size=15),
        }

        self.delete_button = Button((self.pos[0]+self.size[0]-15, self.pos[1]+self.size[1]-15), (30,30), (255,0,0), (255,255,255), "x", border_thickness=3, border_color=(150,0,0), border_radius=5)
        self.add_image_button = Button((self.pos[0]+80, self.pos[1]+71), (40,40), (255,255,255), (0,0,0),"+", border_thickness=3, border_color=(200,200,200), border_radius=5)

        # update placement of all texts on the card
        self.set_pos(self.pos)

    def copy(self):
        return Card(self.name, self.type, self.ca, self.mvt, self.p_perception, self.hp, self.attributes, self.txt, self.size, self.pos, self.image)

    def save(self):
        return {
            "name":self.name,
            "type":self.type,
            "ca":self.ca,
            "mvt":self.mvt,
            "p_perception":self.p_perception,
            "hp":self.hp,
            "attributes":self.attributes,
            "txt":self.txt,
            "size":self.size,
            "pos":self.pos,
            "image":pygame.image.tostring(self.image, "RGBA").hex(),
            "image_size":self.image.get_size()
        }

    def stop_editing(self):
        if self.editing == "": return
        if self.editing == "type": self.type = self.text_fields[self.editing].text
        if self.editing == "name": self.name = self.text_fields[self.editing].text
        if self.editing == "ca": self.ca = self.text_fields[self.editing].text
        if self.editing == "mvt": self.mvt = self.text_fields[self.editing].text
        if self.editing == "p_perception": self.p_perception = self.text_fields[self.editing].text
        if self.editing == "hp": self.hp = self.text_fields[self.editing].text
        if self.editing == "str": self.attributes["str"] = self.text_fields[self.editing].text
        if self.editing == "dex": self.attributes["dex"] = self.text_fields[self.editing].text
        if self.editing == "con": self.attributes["con"] = self.text_fields[self.editing].text
        if self.editing == "int": self.attributes["int"] = self.text_fields[self.editing].text
        if self.editing == "wis": self.attributes["wis"] = self.text_fields[self.editing].text
        if self.editing == "cha": self.attributes["cha"] = self.text_fields[self.editing].text

        if self.editing == "txt1": self.txt[0] = self.text_fields[self.editing].text
        if self.editing == "txt2": self.txt[1] = self.text_fields[self.editing].text
        if self.editing == "txt3": self.txt[2] = self.text_fields[self.editing].text
        if self.editing == "txt4": self.txt[3] = self.text_fields[self.editing].text

        self.text_fields[self.editing].is_edited = False
        self.editing = ""
        global card_edited, object_edited
        card_edited = -1
        object_edited = ""

    def load_image(self):
        path = fileopenbox()
        
        raw_image = pygame.image.load_extended(path).convert_alpha()
        raw_size = raw_image.get_size()
        ratio = raw_size[1]/raw_size[0]
        raw_image = pygame.transform.smoothscale(raw_image, (170, 170*ratio))
        self.image.blit(pygame.Surface((170,170)), (0,0))
        self.image.blit(raw_image, (0,0))

    def edit(self, event):
        if self.editing != "" and not self.text_fields[self.editing].write(event):
            self.stop_editing()
    
    def set_name(self, name):
        self.text_fields["name"].set_text(name)
        self.name = name

    def click(self):
        if pygame.mouse.get_pressed()[0] and not mb1_down:
            mouse_pos = pygame.mouse.get_pos()
            return mouse_pos[0] >= self.pos[0] and mouse_pos[0] <= self.pos[0]+self.size[0] and mouse_pos[1] >= self.pos[1] and mouse_pos[1] <= self.pos[1]+self.size[1]

    def mouse_over(self):
        mouse_pos = pygame.mouse.get_pos()
        return mouse_pos[0] >= self.pos[0] and mouse_pos[0] <= self.pos[0]+self.size[0] and mouse_pos[1] >= self.pos[1] and mouse_pos[1] <= self.pos[1]+self.size[1]

    def drag(self, offset):
        # move the card
        w, h = pygame.display.get_surface().get_size()
        mouse_pos = pygame.mouse.get_pos()
        self.pos = [min(max(mouse_pos[0]+offset[0], 0), w-self.size[0]), min(max(mouse_pos[1]+offset[1], 0), self.pos[1]+50)]
        # move its elements
        self.set_pos(self.pos)

    def set_pos(self, pos):
        self.pos = pos
        self.delete_button.pos = (self.pos[0]+self.size[0]-15, self.pos[1]+self.size[1]-15)
        self.image_pos = (self.pos[0]+15, self.pos[1]+35)
        self.add_image_button.pos = (self.pos[0]+80, self.pos[1]+71)

        self.text_fields["name"].pos = (self.pos[0]+45, self.pos[1]+13)

        self.text_fields["type"].pos = (self.pos[0]+25-self.text_fields["type"].current_width//2, self.pos[1]+15) 
        self.text_fields["ca"].pos = (self.pos[0]+40-self.text_fields["ca"].current_width//2, self.pos[1]+152) 
        if self.type in ["mtr", "bss"]: self.text_fields["mvt"].pos = (self.pos[0]+79-self.text_fields["mvt"].current_width//2, self.pos[1]+156) 
        else: self.text_fields["mvt"].pos = (self.pos[0]+75-self.text_fields["mvt"].current_width//2, self.pos[1]+152) 
        self.text_fields["p_perception"].pos = (self.pos[0]+119-self.text_fields["p_perception"].current_width//2, self.pos[1]+152) 
        self.text_fields["hp"].pos = (self.pos[0]+159-self.text_fields["hp"].current_width//2, self.pos[1]+150) 
        self.text_fields["str"].pos = (self.pos[0]+30-self.text_fields["str"].current_width//2, self.pos[1]+193) 
        self.text_fields["dex"].pos = (self.pos[0]+58-self.text_fields["dex"].current_width//2, self.pos[1]+193) 
        self.text_fields["con"].pos = (self.pos[0]+86-self.text_fields["con"].current_width//2, self.pos[1]+193) 
        self.text_fields["int"].pos = (self.pos[0]+114-self.text_fields["int"].current_width//2, self.pos[1]+193) 
        self.text_fields["wis"].pos = (self.pos[0]+142-self.text_fields["wis"].current_width//2, self.pos[1]+193) 
        self.text_fields["cha"].pos = (self.pos[0]+170-self.text_fields["cha"].current_width//2, self.pos[1]+193) 
        self.text_fields["txt1"].pos = (self.pos[0]+20,self.pos[1]+self.size[1]-68)
        self.text_fields["txt2"].pos = (self.pos[0]+20,self.pos[1]+self.size[1]-50)
        self.text_fields["txt3"].pos = (self.pos[0]+20,self.pos[1]+self.size[1]-32)

    def render(self):
        w, h = pygame.display.get_surface().get_size()

        self.set_pos(self.pos)

        # prevent from exiting the screen on the x axis
        if self.pos[0] < 0:
            self.set_pos((0, self.pos[1]))
        elif self.pos[0]+self.size[0] > w:
            self.set_pos((w-self.size[0], self.pos[1]))

        # prevent from exiting the screen on the y axis
        if not deck_menu_opened:
            if self.pos[1] < 0:
                self.seet_pos((self.pos[0], 0))
            elif self.pos[1]+50 > h:
                self.set_pos((self.pos[0], h+50-self.size[1]))

        screen.blit(self.image, self.image_pos)

        texture_index = self.type+"_card" if self.type+"_card" in texture_atlas.keys() else "default_card"
        screen.blit(texture_atlas[texture_index], self.pos)
        
        key_pressed = pygame.key.get_pressed()
        if (key_pressed[pygame.K_LSHIFT] or key_pressed[pygame.K_RSHIFT]) and object_edited=="":
            self.delete_button.render()
            if deck_menu_opened == -1: 
                self.add_image_button.render()

        if self.text_fields["type"].is_edited: self.text_fields["type"].pos = (self.pos[0]+25-self.text_fields["type"].current_width//2, self.pos[1]+15) 
        elif self.text_fields["ca"].is_edited: self.text_fields["ca"].pos = (self.pos[0]+40-self.text_fields["ca"].current_width//2, self.pos[1]+152) 
        elif self.text_fields["mvt"].is_edited: self.text_fields["mvt"].pos = (self.pos[0]+75-self.text_fields["mvt"].current_width//2, self.pos[1]+152) 
        elif self.text_fields["p_perception"].is_edited: self.text_fields["p_perception"].pos = (self.pos[0]+119-self.text_fields["p_perception"].current_width//2, self.pos[1]+152) 
        elif self.text_fields["hp"].is_edited: self.text_fields["hp"].pos = (self.pos[0]+159-self.text_fields["hp"].current_width//2, self.pos[1]+150) 
        elif self.text_fields["str"].is_edited: self.text_fields["str"].pos = (self.pos[0]+30-self.text_fields["str"].current_width//2, self.pos[1]+193) 
        elif self.text_fields["dex"].is_edited: self.text_fields["dex"].pos = (self.pos[0]+58-self.text_fields["dex"].current_width//2, self.pos[1]+193) 
        elif self.text_fields["con"].is_edited: self.text_fields["con"].pos = (self.pos[0]+86-self.text_fields["con"].current_width//2, self.pos[1]+193) 
        elif self.text_fields["int"].is_edited: self.text_fields["int"].pos = (self.pos[0]+114-self.text_fields["int"].current_width//2, self.pos[1]+193) 
        elif self.text_fields["wis"].is_edited: self.text_fields["wis"].pos = (self.pos[0]+142-self.text_fields["wis"].current_width//2, self.pos[1]+193) 
        elif self.text_fields["cha"].is_edited: self.text_fields["cha"].pos = (self.pos[0]+170-self.text_fields["cha"].current_width//2, self.pos[1]+193) 

        for tf in self.text_fields.keys():
            self.text_fields[tf].render()
        

class Button:
    def __init__(self, pos=[0,0], size=[25,25], bg_color=[255,255,255], text_color=[0,0,0], text="button", font="Arial", font_size=30, border_thickness=0, border_color=[0,0,0], border_radius=0) -> None:
        self.pos = list(pos)
        self.size = list(size)
        self.bg_color = list(bg_color)
        self.text_color = list(text_color)
        self.text = text
        self.font = font
        self.font_size = font_size
        self.border_thickness = border_thickness
        self.border_color = list(border_color)
        self.border_radius = border_radius
    

    def mouse_over(self):
        mouse_pos = pygame.mouse.get_pos()
        return mouse_pos[0] >= self.pos[0] and mouse_pos[0] <= self.pos[0]+self.size[0] and mouse_pos[1] >= self.pos[1] and mouse_pos[1] <= self.pos[1]+self.size[1]

    def click(self):
        if pygame.mouse.get_pressed()[0] and not mb1_down:
            mouse_pos = pygame.mouse.get_pos()
            return mouse_pos[0] >= self.pos[0] and mouse_pos[0] <= self.pos[0]+self.size[0] and mouse_pos[1] >= self.pos[1] and mouse_pos[1] <= self.pos[1]+self.size[1]

    def render(self):
        font = pygame.font.SysFont(self.font, self.font_size)

        pygame.draw.rect(screen, self.bg_color, pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1]), border_radius=self.border_radius)
        if self.border_thickness > 0:
            pygame.draw.rect(screen, self.border_color, pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1]), self.border_thickness, border_radius=self.border_radius)
        text = font.render(self.text, True, self.text_color)
        screen.blit(text, (int(self.pos[0]+self.size[0]/2-font.size(self.text)[0]/2), int(self.pos[1]+self.size[1]/2-font.size(self.text)[1]/2)))


class Deck:
    def __init__(self, title, pos_number):
        w, h = screen.get_size()
        self.cards = list()
        self.pos_number = pos_number
        self.size = (200, 100)
        self.pos = (w/7*self.pos_number + w/14-self.size[0]/2, h-50)
        title_text_size = arial.size(title)[0]
        self.title = TextField(title, (self.pos[0]+self.size[0]/2-title_text_size/2, h-80), 180, font_size=20)

        self.is_menu_opened = False
        self.save_button = Button((w/2-70, h-70), (60,60), text="Save", font_size=20, border_radius=5)
        self.load_button = Button((w/2+10, h-70), (60,60), text="Load", font_size=20, border_radius=5)

        self.is_saved = False

    def save(self):
        cards_to_save = list()
        for card in self.cards:
            cards_to_save.append(card.save())
        
        data_to_save = {
            "title":self.title.text,
            "cards":cards_to_save
        }

        save_as = filesavebox(default="*/*.deck", filetypes="*.deck")
        if save_as:
            with open(save_as, "w") as file:
                file.write(dumps(data_to_save))
            self.is_saved = True

    def mouse_over(self, y_offset=0):
        mouse_pos = pygame.mouse.get_pos()
        return mouse_pos[0] >= self.pos[0] and mouse_pos[0] <= self.pos[0]+self.size[0] and mouse_pos[1] >= self.pos[1]+y_offset and mouse_pos[1] <= self.pos[1]+self.size[1]
        
    def stop_editing(self):
        global deck_edited, object_edited
        deck_edited = -1
        object_edited = ""
        self.title.is_edited = False

    def edit(self, event):
        if not self.title.write(event):
            self.stop_editing()
    
    def click(self):
        if pygame.mouse.get_pressed()[0] and not mb1_down:
            mouse_pos = pygame.mouse.get_pos()
            return mouse_pos[0] >= self.pos[0] and mouse_pos[0] <= self.pos[0]+self.size[0] and mouse_pos[1] >= self.pos[1] and mouse_pos[1] <= self.pos[1]+self.size[1]

    def rescale(self, w, h):
        if self.is_menu_opened:
            self.save_button.pos = (w/2-70, h-70)
            self.load_button.pos = (w/2+10, h-70)
        self.pos = (w/7*self.pos_number + w/14-self.size[0]/2, h-50)
        title_text_size = arial.size(self.title.text)[0]
        self.title.pos = (self.pos[0]+self.size[0]/2-title_text_size/2, h-80)


    def render_menu(self, scroll_amount):
        w, h = screen.get_size()
        n_columns = max((w-200)//230, 1)
        n_rows = ceil(len(self.cards)/n_columns)

        scroll_amount = min(0, max(scroll_amount, -(200+15+315*n_rows)+h))
        len_deck = len(self.cards)-1

        card_index = 0
        for row in range(n_rows):
            for col in range(n_columns):
                self.cards[card_index].set_pos((w/2-115*n_columns+30+215*col, 100+15+315*row+scroll_amount))
                # if card is visible
                if self.cards[card_index].pos[1] < h and self.cards[card_index].pos[1]+self.cards[card_index].size[1] > 0: 
                    self.cards[card_index].render() # render card
                
                if card_index < len_deck: card_index += 1
                else: break
        
        self.save_button.render()
        self.load_button.render()

        return scroll_amount

    def render(self, y_offset=0):
        deck_texture = "deck_"+str(min(len(self.cards), 3))
        screen.blit(texture_atlas[deck_texture], (self.pos[0], self.pos[1]+y_offset))

        self.title.render((0,y_offset))

        if y_offset < 0:
            # show number of cards
            w, h = pygame.display.get_surface().get_size()
            s = "s" if len(self.cards)!=1 else ""
            card_number_text = arial_15.render(str(len(self.cards))+" card"+s, True, (0,0,0))
            card_number_text_size = arial_15.size(str(len(self.cards))+" card"+s)[0]
            screen.blit(card_number_text, (self.pos[0]+self.size[0]/2-card_number_text_size/2, h+20+y_offset))


# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #
#              INITIALISATION             #
# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #

#new_card_button = Button((WIDTH/2-70, HEIGHT-70), (60,60), text="+", font_size=60, border_radius=5)
#menu_button = Button((WIDTH/2+10, HEIGHT-70), (60,60), text="Menu", font_size=20, border_radius=5)
new_card_button = Button((WIDTH/2-30, HEIGHT-70), (60,60), text="+", font_size=60, border_radius=5)

close_menu_button = Button((WIDTH-70, 20), (50,50), (150,150,150), text="X", border_radius=10)

# different decks
decks = [
    Deck("Deck 1", 0),
    Deck("Deck 2", 1),
    Deck("Deck 3", 2),
    Deck("Deck 4", 4),
    Deck("Deck 5", 5),
    Deck("Deck 6", 6),
]

# menu scroll
scroll_amount=0
scroll_sensitivity = 25

texture_atlas = resize_textures()


# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #
#                EXÉCUTION                #
# ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ ♥ #

# I'm confused on this one, but somehow, while 1 is faster than while True (although not by a lot with python 3.x.x)
while 1:

    w, h = pygame.display.get_surface().get_size()

    key_pressed = pygame.key.get_pressed()

    # ======================= EVENT LOOP ======================= #
    for event in pygame.event.get():
        #Si petite croix cliqué -> fermer le programme
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        elif event.type == pygame.KEYDOWN:
            if card_edited > -1 and object_edited == "card" and deck_menu_opened == -1:
                cards[card_edited].edit(event)
                update_display = True
            elif deck_edited > -1 and object_edited == "deck" and deck_menu_opened == -1:
                decks[deck_edited].edit(event)
                update_display = True
            elif event.key == pygame.K_ASTERISK:
                show_debug_info = True if not show_debug_info else False
                update_display = True
            elif event.key == pygame.K_ESCAPE and deck_menu_opened > -1:
                if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                decks[deck_menu_opened].is_menu_opened = False
                deck_menu_opened = -1
                update_display = True
        
        # drop card in the deck
        elif event.type == pygame.MOUSEBUTTONUP:
            if dragged_card > -1 and deck_menu_opened == -1:
                for deck in decks:
                    if deck.mouse_over():
                        if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                        elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                        deck.cards.append(cards.pop(dragged_card))
                        dragged_card = -1
                        update_display = True
                        break
        
        elif event.type == pygame.MOUSEWHEEL:
            if deck_menu_opened > -1:
                scroll_amount += event.y*scroll_sensitivity
                update_display = True
        
        # update what needs to be updated to fit new window resolution
        elif event.type == pygame.VIDEORESIZE:
            w, h = screen.get_size()
            for deck in decks:
                deck.rescale(w, h)
            new_card_button.pos = ((w/2-30, h-70))
            close_menu_button.pos = (w-70, 20)
            debug_info_x_pos = w-70
            update_display = True

    # ======================= TABLETOP ======================= #
    if deck_menu_opened == -1 :

        scroll_amount=0

        # Add a new card
        if new_card_button.click():
            w, h = screen.get_size()
            card_size = (200,300)
            card = Card(size=card_size, pos=(w/2-card_size[0]/2 + randint(-100,100),h-100-card_size[1]+randint(-100, 10)))
            cards.append(card)
            update_display = True
        
        # deck clicking
        for ii, deck in enumerate(decks):
            if deck.mouse_over(deck_offset[ii]): deck_offset[ii] = -40; update_display = True
            else:
                if deck_offset[ii] == -40: update_display = True
                deck_offset[ii] = 0
            # if click on the name, edit it
            if deck.title.click():
                if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                deck_edited = ii; object_edited = "deck"; deck.title.is_edited = True 
            # else, open deck menu
            elif deck.click():
                if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                deck_menu_opened = ii
                decks[ii].is_menu_opened = True
                update_display = True


        # handle card clicking (starting by the end of the list for the top card)
        for ii in range(len(cards), 0, -1):
            if key_pressed[pygame.K_LSHIFT] or key_pressed[pygame.K_RSHIFT]:
                # if delete_card is clicked
                if cards[ii-1].delete_button.click():
                    if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                    elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                    del cards[ii-1]
                    update_display = True
                    break
                # add image
                elif cards[ii-1].add_image_button.click():
                    if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                    elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                    cards[ii-1].load_image()
                    break
                # copy the card and drag the new card
                elif cards[ii-1].click():
                    if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                    elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                    cards.append(cards[ii-1].copy())
                    mouse_pos = pygame.mouse.get_pos()
                    drag_offset = [cards[ii-1].pos[0]-mouse_pos[0], cards[ii-1].pos[1]-mouse_pos[1]]
                    card = cards.pop(ii-1)
                    cards.append(card)
                    dragged_card = len(cards)-1
                    break
            # checks if a textfield is clicked instead of the card
            text_field_to_edit = ""
            for text_field in cards[ii-1].text_fields.keys():
                if cards[ii-1].text_fields[text_field].click(): 
                    text_field_to_edit = text_field
                    # stop editing the previous card
                    if card_edited > -1 and (ii-1 != card_edited or cards[card_edited].editing != text_field_to_edit):
                        cards[card_edited].stop_editing()
                    break
            # if a textfield is clicked
            if text_field_to_edit != "":
                if object_edited == "deck" and deck_edited > -1:
                    decks[deck_edited].stop_editing()
                cards[ii-1].editing = text_field_to_edit
                cards[ii-1].text_fields[text_field_to_edit].is_edited = True
                card_edited = ii-1
                object_edited = "card"
                break
            # else, initiate dragging
            elif cards[ii-1].click():
                mouse_pos = pygame.mouse.get_pos()
                drag_offset = [cards[ii-1].pos[0]-mouse_pos[0], cards[ii-1].pos[1]-mouse_pos[1]]
                card = cards.pop(ii-1)
                cards.append(card)
                dragged_card = len(cards)-1
                break

            if (key_pressed[pygame.K_LSHIFT] or key_pressed[pygame.K_RSHIFT]) and cards[ii-1].mouse_over() and not cards[ii-1].delete_button.mouse_over() and not cards[ii-1].add_image_button.mouse_over():
                render_copy_context_menu = True
                update_display = True
        
        if dragged_card > -1:
            # drags the card
            cards[dragged_card].drag(drag_offset)

    # ======================= DECK MENU ======================= #
    if deck_menu_opened > -1 and was_deck_menu_opened:

        if close_menu_button.click():
            # close menu
            if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
            elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
            decks[deck_menu_opened].is_menu_opened = False
            deck_menu_opened = -1
            update_display = True
        
        if decks[deck_menu_opened].save_button.click():
            decks[deck_menu_opened].save()

        if decks[deck_menu_opened].load_button.click():
            loaded = load_deck(decks[deck_menu_opened].pos_number)
            if loaded: 
                decks[deck_menu_opened] = loaded

        # handle card clicking (starting by the end of the list for the top card)
        for ii in range(len(decks[deck_menu_opened].cards), 0, -1):
            if key_pressed[pygame.K_LSHIFT] or key_pressed[pygame.K_RSHIFT]:
                # if delete_card is clicked
                if decks[deck_menu_opened].cards[ii-1].delete_button.click():
                    if card_edited > -1: decks[deck_menu_opened].cards[card_edited].stop_editing()
                    del decks[deck_menu_opened].cards[ii-1]

                    # close deck if empty
                    if len(decks[deck_menu_opened].cards) == 0:
                        if object_edited == "card" and card_edited > -1: cards[card_edited].stop_editing()
                        elif object_edited == "deck" and deck_edited > -1: decks[deck_edited].stop_editing()
                        decks[deck_menu_opened].is_menu_opened = False
                        deck_menu_opened = -1
                    update_display = True
                    break

            # start dragging and exit menu
            if decks[deck_menu_opened].cards[ii-1].click():

                if key_pressed[pygame.K_LSHIFT] or key_pressed[pygame.K_RSHIFT]: 
                    cards.append(decks[deck_menu_opened].cards[ii-1].copy())
                else: cards.append(decks[deck_menu_opened].cards.pop(ii-1))
                decks[deck_menu_opened].is_menu_opened = False
                deck_menu_opened = -1

                mouse_pos = pygame.mouse.get_pos()
                drag_offset = [cards[-1].pos[0]-mouse_pos[0], cards[-1].pos[1]-mouse_pos[1]]
                dragged_card = len(cards)-1
                update_display = True
                break

            if (key_pressed[pygame.K_LSHIFT] or key_pressed[pygame.K_RSHIFT]) and decks[deck_menu_opened].cards[ii-1].mouse_over() and not decks[deck_menu_opened].cards[ii-1].delete_button.mouse_over():
                render_copy_context_menu = True
                update_display = True

    was_deck_menu_opened = deck_menu_opened > -1

    mb1_down = pygame.mouse.get_pressed()[0]
    mb2_down = pygame.mouse.get_pressed()[1]
    mb3_down = pygame.mouse.get_pressed()[2]
    if not mb1_down: dragged_card = -1

    # ======================= RENDER ======================= #
    w, h = pygame.display.get_surface().get_size()

    if is_shift_pressed: update_display = True
    if key_pressed[pygame.K_LSHIFT] or key_pressed[pygame.K_RSHIFT]: is_shift_pressed = True
    else : is_shift_pressed = False


    
    if object_edited != "": update_display = True
    if dragged_card > -1: update_display = True

    if update_display:
        screen.fill((0,170,0))
        for ii, deck in enumerate(decks):
            deck.render(deck_offset[ii])

        for card in cards:
            card.render()
    
        new_card_button.render()


        if deck_menu_opened > -1:
            draw_rect_alpha(screen, (50,50,50,200), pygame.Rect(0,0,w,h))
            close_menu_button.render()

            scroll_amount = decks[deck_menu_opened].render_menu(scroll_amount)

        if render_copy_context_menu and object_edited == "":
            mouse_pos = pygame.mouse.get_pos()
            copy_notification_text = arial.render("copy", True, (0,0,0), (255,255,255))
            cnt_size = copy_notification_text.get_size()[0]
            screen.blit(copy_notification_text, (mouse_pos[0]-cnt_size/2, mouse_pos[1]-20))
            render_copy_context_menu = False

        if show_debug_info:
            fps_display = arial.render(str(int(pygame_clock.get_fps()))+" fps", True, (0,0,0))
            nb_cards = arial.render(str(len(cards))+" cards", True, (0,0,0))
            screen.blit(fps_display, (debug_info_x_pos, 10))
            screen.blit(nb_cards, (debug_info_x_pos, 30))
        
        update_display = False

        pygame.display.update()
    
    deltaTime = pygame_clock.tick(maxFPS)