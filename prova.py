import tkinter as tk
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from PIL import ImageDraw

class Zoom_Advanced(ttk.Frame):
    def __init__(self, mainframe, path):
        ''' Initialize the main Frame '''
        ttk.Frame.__init__(self, master=mainframe)
        self.master.title('Mask Generator')
        # Create canvas and put image on it
        self.canvas = tk.Canvas(self.master, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        # Make the canvas expandable
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.wheel)  # only with Linux, wheel scroll up
        self.canvas.bind('<Button-1>',self.inizio_selezione)
        self.canvas.bind('<B1-Motion>',self.selezione_in_corso)
        self.canvas.bind('<ButtonRelease-1>',self.fine_selezione)
        
        #do possibilita di fare undo e reset anche con la combinazione di tasti ctrl+z e ctrl+r
        self.canvas.bind_all("<Control-z>", self.undo)
        self.canvas.bind_all("<Control-r>", self.reset_dimensioni)

        # Add a frame for radio buttons
        self.radio_frame = ttk.Frame(self.master)
        self.radio_frame.grid(row=2, column=0, sticky='w')

        self.radio_var = tk.StringVar()
        oval_radio = ttk.Radiobutton(self.radio_frame, text='Cerchio', variable=self.radio_var, value='c')
        oval_radio.grid(row=0, column=0, padx=5, pady=5)
        rect_radio = ttk.Radiobutton(self.radio_frame, text='Rettangolo', variable=self.radio_var, value='r')
        rect_radio.grid(row=0, column=1, padx=5, pady=5)
        poly_radio = ttk.Radiobutton(self.radio_frame, text='Poligono', variable=self.radio_var, value='p')
        poly_radio.grid(row=0, column=2, padx=5, pady=5)
       
        self.radio_var.set("c")#all'inizio scelgo in automatico impostando al cerchio

        #Bottone per fare il reset
        bottone_reset=ttk.Button(self.radio_frame,text='Reset',command=self.reset_dimensioni)
        bottone_reset.grid(row=0,column=3)

        #Bottone per fare l'undo
        bottone_undo=ttk.Button(self.radio_frame,text="Undo",command=self.undo)
        bottone_undo.grid(row=0,column=4)

        #Bottone per generare maschera
        bottone_mask = ttk.Button(self.radio_frame, text='Crea mask', command=self.genera_mask)
        bottone_mask.grid(row=0, column=5)

        #Bottone per caricare una nuova immagine
        bottone_carica_imm=ttk.Button(self.radio_frame,text="Nuova immagine",command=self.carica)
        bottone_carica_imm.grid(row=0,column=6)

        #lista per mantenere disegni per poter fare undo
        self.coord_disegni=[]
        self.punti_poligoni=[]
        self.tmp_poly_created = False
        self.image = Image.open(path)  # apre immagine
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        # Metto l'immagine in un rettangolo che fa da contenitore e 
        #lo uso per settare le giuste coordinate all'immagine e sfruttarle per lo zoom
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        #faccio un controllo sulle dimensioni per fare in modo di aprire una finestra che non mi faccia perdere nessun bottone
        self.dim_minima=580;
        if(self.width>=self.dim_minima):
            self.master.geometry(f"{self.width}x{self.height}")
        else:
            self.master.geometry(f"{self.dim_minima}x{self.height}")            
        self.show_image()
        
    def reset_dimensioni(self,event=None):
        self.width, self.height = self.image.size
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3 # zoom magnitude
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.reset_disegni()
        self.show_image()

    def carica(self):
        self.reset_disegni()
        percorso_foto=filedialog.askopenfilename()
        nuova_imm=Image.open(percorso_foto)
        self.width, self.height = nuova_imm.size
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        self.image=nuova_imm
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        if(self.width>=self.dim_minima):
            self.master.geometry(f"{self.width}x{self.height}")
        else:
            self.master.geometry(f"{self.dim_minima}x{self.height}")  
        self.show_image()

    def e_dentro_immagine(self, x, y):
        bbox = self.canvas.bbox(self.container)  # Ottengo il bounding box dell'immagine
        return bbox[0] <= x <= bbox[2] and bbox[1] <= y <= bbox[3]

    def selezione_in_corso(self,event):
        if self.radio_var.get()=="c" and self.e_dentro_immagine(self.inizio_x,self.inizio_y):#se i punti iniziali fossero fuori l'area dell'immagine non farei nessun disegno
            if self.e_dentro_immagine(event.x,event.y):
                self.canvas.delete("cerchio_temporaneo")
                self.canvas.create_oval(self.inizio_x, self.inizio_y, event.x, event.y, outline="red", tags="cerchio_temporaneo")
            else: #se l'utente disegna fuori dall'area dell'immagine elimino il temporaneo e non vado avanti cosi non viene creato 
                self.canvas.delete("cerchio_temporaneo")
        if self.radio_var.get()=="r" and self.e_dentro_immagine(self.inizio_x,self.inizio_y):
            if self.e_dentro_immagine(event.x,event.y):
                self.canvas.delete("rettangolo_temporaneo")
                self.canvas.create_rectangle(self.inizio_x, self.inizio_y, event.x, event.y, outline="red", tags="rettangolo_temporaneo")
            else:
                self.canvas.delete("rettangolo_temporaneo")
        if self.radio_var.get()=="p" and self.e_dentro_immagine(self.inizio_x,self.inizio_y):
            if self.e_dentro_immagine(event.x,event.y):
                #self.canvas.delete("poligono_temporaneo")
                if self.tmp_poly_created:
                    self.canvas.delete(self.tmp_poly)
                self.poly_punti.append((event.x, event.y))
                self.tmp_poly = self.canvas.create_line(self.poly_punti, fill="red", tags="poligono_temporaneo")
                #print(self.canvas.coords(self.tmp_poly))
                self.tmp_poly_created=True
                #self.punti_poligoni[-1].append((event.x,event.y))
            else:
                self.canvas.delete("poligono_temporaneo")
                self.tmp_poly_created=False

    def inizio_selezione(self, event):
            self.inizio_x = event.x 
            self.inizio_y = event.y
            #self.poly_punti = [(event.x, event.y)]
            #self.tmp_poly = None
            if(self.radio_var.get()=='p'):
                self.poly_punti = [(event.x, event.y)]
                #self.punti_poligoni.append([(event.x,event.y)])
                #print(self.punti_poligoni)
                #print(self.punti_poligoni[-1])
                


    def fine_selezione(self, event):
        bbox = self.canvas.bbox(self.container)  # Ottengo il bounding box dell'immagine
        vertici_imm = [bbox[0], bbox[1], bbox[2], bbox[3]]  # vertici dell'immagine nel canvas
        x_1=((self.inizio_x-(vertici_imm[0]))*self.width)/(vertici_imm[2]-vertici_imm[0])#proporzione per adattare le coordinate dei disegni fatti con lo zoom alla loro posizione rispetto l'immagine iniziale
        y_1=((self.inizio_y-(vertici_imm[1]))*self.height)/(vertici_imm[3]-vertici_imm[1])
        x_2=((event.x-(vertici_imm[0]))*self.width)/(vertici_imm[2]-vertici_imm[0])
        y_2=((event.y-(vertici_imm[1]))*self.height)/(vertici_imm[3]-vertici_imm[1])
        if self.radio_var.get() == "c" and self.e_dentro_immagine(event.x,event.y) and self.e_dentro_immagine(self.inizio_x,self.inizio_y):#se non sono dentro l'immagine i vertici non creo nulla
            self.canvas.delete("cerchio_temporaneo")
            cerc = self.canvas.create_oval(self.inizio_x, self.inizio_y, event.x, event.y, outline="red", tags="cerchio")
            self.coord_disegni.append(("cerchio",x_1,y_1,x_2,y_2,cerc,self.imscale))
            #print("fine "+str(event.x)+","+str(event.y))
        elif self.radio_var.get() == "r" and self.e_dentro_immagine(event.x,event.y) and self.e_dentro_immagine(self.inizio_x,self.inizio_y):
            self.canvas.delete("rettangolo_temporaneo")
            rett = self.canvas.create_rectangle(self.inizio_x, self.inizio_y, event.x, event.y, outline="red", tags="rettangolo")
            self.coord_disegni.append(("rettangolo", x_1,y_1,x_2, y_2, rett, self.imscale))
        elif self.radio_var.get() == "p" and self.e_dentro_immagine(event.x,event.y) and self.e_dentro_immagine(self.inizio_x,self.inizio_y):
            #self.canvas.delete("poligono_temporaneo")
            if self.tmp_poly_created:
                self.canvas.delete(self.tmp_poly)
            self.poly_punti.append((event.x, event.y))
            polig=self.canvas.create_polygon(self.poly_punti, outline="red", tags="poligono",fill="")
            self.punti_poligoni.append(self.poly_punti)
            self.coord_disegni.append(("poligono", x_1,y_1,x_2, y_2,polig, self.imscale))
            #vertici rettangolo che circoscrive poligono, lo disegno sulla canva solo per visualizzarlo ora, poi lo tolgo
            #inoltre posso fare una chiamata a funzione per calcolare queste coordinate rendendo il codice piu leggibile
            min_x=self.poly_punti[0][0]
            max_x=self.poly_punti[0][0]
            min_y=self.poly_punti[0][1]
            max_y=self.poly_punti[0][1]
            for (cord_x,cord_y) in self.poly_punti:
                if cord_x<min_x:
                    min_x=cord_x
                elif cord_x>max_x:
                    max_x=cord_x
                if cord_y<min_y:
                    min_y=cord_y
                elif cord_y>max_y:
                    max_y=cord_y       
            #rett = self.canvas.create_rectangle(min_x, min_y, max_x,max_y, outline="red", tags="rettangolo")
            print(self.canvas.coords(polig))
            punti_poligono=self.canvas.coords(polig)
            
            
            
            #se servono qui ho stampe dei vertici del mio rettangolo
            #print(min_x,min_y)
            #print(max_x,max_y)
            print("----------------------------COORDINATE ULTIMO POLIGONO DISEGNATO-----------------------------")
            print(self.punti_poligoni[-1])
            print("-------------------------------LISTA COORD DI TUTTI I POLIGONI DISEGNATI------------------------")
            print(self.punti_poligoni)
            

    def reset_disegni(self,event=None):
        #da qui potrei anche togliere i temporanei perche tanto non ce ne sono, pero fallo poi e fai prove
        self.canvas.delete("cerchio")
        self.canvas.delete("cerchio_temporaneo")
        self.canvas.delete("rettangolo")
        self.canvas.delete("rettangolo_temporaneo")
        self.canvas.delete("poligono")
        self.canvas.delete("poligono_temporaneo")
        self.coord_disegni.clear()
        self.punti_poligoni.clear()#non devono rimanere poligoni nella mia lista


    def genera_mask(self):
        # Inizializzo una matrice numpy con tutti gli elementi impostati su 0 (tutto nero)
        mask = np.zeros((self.height, self.width), dtype=np.uint8)
        for shape,x1,y1,x2,y2,_,_ in self.coord_disegni:
            if shape=="cerchio":
                centro_x=int((x1+x2)/2)
                centro_y=int((y1+y2)/2)
                print("centro "+str(centro_x)+","+str(centro_y))
                a=0.5*np.sqrt((x2-x1)*(x2-x1))
                b=0.5*np.sqrt((y2-y1)*(y2-y1))
                print("a e b rispett: "+str(a)+","+str(b))
                if x1<=x2:#disegno da sx verso dx
                    for x in range(int(x1), int(x2+ 1)):
                        if y1<=y2:#disegno fatto da alto verso basso
                            for y in range(int(y1), int(y2 + 1)):
                                if (((x-centro_x)*(x-centro_x))/(a*a))+(((y-centro_y)*(y-centro_y))/(b*b)) <= 1:
                                    mask[y,x]=1
                        else:#disegno fatto da basso verso alto
                            for y in range(int(y2), int(y1 + 1)):
                                if (((x-centro_x)*(x-centro_x))/(a*a))+(((y-centro_y)*(y-centro_y))/(b*b)) <= 1:
                                    mask[y,x]=1     
                else:#disegno fatto da dx verso sx
                    for x in range(int(x2), int(x1+ 1)):
                        if y1<=y2:#da alto verso basso
                            for y in range(int(y1), int(y2 + 1)):
                                if (((x-centro_x)*(x-centro_x))/(a*a))+(((y-centro_y)*(y-centro_y))/(b*b)) <= 1:
                                    mask[y,x]=1
                        else:#da basso verso alto
                            for y in range(int(y2), int(y1 + 1)):
                                if (((x-centro_x)*(x-centro_x))/(a*a))+(((y-centro_y)*(y-centro_y))/(b*b)) <= 1:
                                    mask[y,x]=1 
            elif shape=="rettangolo":
                if x1<=x2:#casi identici all'ellisse
                    if y1<=y2:
                        mask[int(y1):int(y2), int(x1):int(x2)] = 1
                    else:
                        mask[int(y2):int(y1), int(x1):int(x2)] = 1
                else:
                    if y1<=y2:
                        mask[int(y1):int(y2), int(x2):int(x1)] = 1
                    else:
                        mask[int(y2):int(y1), int(x2):int(x1)] = 1
            else:
                for poligono in self.punti_poligoni:
                    for coppia in range(len(poligono)-1):#voglio escludere ultima coppia perche va accoppiata col primo elemento
                        self.calcola_punti_retta(poligono[coppia],poligono[coppia+1],mask)
                    self.calcola_punti_retta(poligono[0],poligono[-1],mask)
                    lista_interni=self.points_inside_polygon(poligono)
                    for coppia in lista_interni:
                        mask[coppia[1],coppia[0]]=1
        mask_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if mask_path:
            Image.fromarray(mask * 255).save(mask_path)

    def is_point_inside_polygon(self,x, y, poly):
        """
        Verifica se il punto (x, y) è all'interno del poligono poly.
        poly è una lista di tuple rappresentanti i vertici del poligono.
        Restituisce True se il punto è all'interno del poligono, altrimenti False.
        """
        n = len(poly)
        inside = False
        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    def points_inside_polygon(self,poly):
        """
        Restituisce una lista di tuple rappresentanti i punti interni al poligono poly.
        poly è una lista di tuple rappresentanti i vertici del poligono.
        """
        min_x = min(poly, key=lambda p: p[0])[0]
        max_x = max(poly, key=lambda p: p[0])[0]
        min_y = min(poly, key=lambda p: p[1])[1]
        max_y = max(poly, key=lambda p: p[1])[1]
        points = []
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if self.is_point_inside_polygon(x, y, poly):
                    points.append((x, y))
        return points


    def calcola_punti_retta(self,p1,p2,mask):
        x1,y1=p1
        x2,y2=p2
        ''' if(x2==x1):#retta verticale
            for y in range(min(y1,y2),max(y1,y2)+1):
                mask[y,x1]=1
        elif(y2==y1):#retta orizzontale
            for x in range(min(x1,x2),max(x1,x2)+1):
                mask[y2,x]=1
        else:#retta obliqua
            for y in range(y_min,y_max+1):
                for x in range(x_min,x_max+1):
                    if(((x-x1)/(x2-x1))==((y-y1)/(y2-y1))):
                        mask[y,x]=1
        mask[y1,x1]=1'''
        points = []
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            points.append((x1, y1))
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
        for punti in points:
            mask[punti[1],punti[0]]=1
            


    def undo(self,event=None):
        if len(self.coord_disegni)==0:
            print("vuoto")
            return
        ultimo_disegno=self.coord_disegni[-1]
        if(ultimo_disegno[0]=="poligono"):#se l'ultimo disegno fatto era un poligono lo rimuovo anche dalla lista dei poligoni
            self.punti_poligoni.remove(self.punti_poligoni[-1])
        self.canvas.delete(ultimo_disegno[5])#elimino con id
        self.coord_disegni.remove(ultimo_disegno)
        

    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        self.show_image()
        

    def show_image(self, event=None):
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection
        self.master.focus_force()#metto in primo piano la finestra

#percorso_foto=filedialog.askopenfilename()
root = tk.Tk()
#app = Zoom_Advanced(root, path=percorso_foto)
app = Zoom_Advanced(root, "vite.jpg")
root.mainloop()