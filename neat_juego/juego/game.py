import pygame
import math

pygame.init()

#class gameInformation:
#  def __init__ (self):
     

class Jugador:
    Vel = 3
    x: int
    y: int
    choco_con_pared = False
    def __init__(self, x, y,imagen_jugador):
        self.rect = pygame.Rect(x, y, 34, 34)
        self.image = imagen_jugador
        self.x= x
        self.y = y

    def mover(self, keys, paredes):
        dx = dy = 0
        if keys[pygame.K_w]:
            dy -= self.Vel
        if keys[pygame.K_s]:
            dy += self.Vel
        if keys[pygame.K_a]:
            dx -= self.Vel
        if keys[pygame.K_d]:
            dx += self.Vel

        # Mover y detectar colisión horizontal
        self.rect.x += dx
        for pared in paredes:
            if self.rect.colliderect(pared):
                self.rect.x -= dx  # deshacer

        # Mover y detectar colisión vertical
        self.rect.y += dy
        for pared in paredes:
          if self.rect.colliderect(pared):
            self.rect.y -= dy  # deshacer

    #mover IA
    def mover_desde_ia(self, salida, paredes):
      self.choco_con_pared = False

      # salida: [o0, o1, o2]
      o0, o1, o2 = salida[0], salida[1], salida[2]

      # Decisión de moverse: si la red usa tanh ([-1,1]) -> umbral 0 ; si usa sigmoid ([0,1]) -> umbral 0.5.
      # Usamos un umbral intermedio 0.0 para ser robustos a ambas.
      mover = o2 > 0.0

      dx = dy = 0.0
      if mover:
          # Detectar si las salidas parecen estar en [-1,1] o en [0,1]
          if -1.01 < o0 < 1.01 and -1.01 < o1 < 1.01:
              # parecen tanh -> ya están en [-1,1]
              dx = o0 * self.Vel
              dy = o1 * self.Vel
          else:
              # parecen estar en [0,1] -> mapear a [-1,1]
              dx = (o0 * 2 - 1) * self.Vel
              dy = (o1 * 2 - 1) * self.Vel

          vec = pygame.Vector2(dx, dy)
          if vec.length() > 0:
              vec = vec.normalize() * self.Vel
              dx, dy = vec.x, vec.y

      # --- resolución de colisión por ejes (slide) ---
      # Horizontal
      self.rect.x += int(round(dx))
      collided = [p for p in paredes if self.rect.colliderect(p.rect)]
      for p in collided:
          self.choco_con_pared = True
          if dx > 0:
              self.rect.right = p.rect.left
          elif dx < 0:
              self.rect.left = p.rect.right

      # Vertical
      self.rect.y += int(round(dy))
      collided = [p for p in paredes if self.rect.colliderect(p.rect)]
      for p in collided:
          self.choco_con_pared = True
          if dy > 0:
              self.rect.bottom = p.rect.top
          elif dy < 0:
              self.rect.top = p.rect.bottom

      self.x = self.rect.x
      self.y = self.rect.y

    def sensor_enemigos(self, enemigos, max_dist=200):
      """
      Retorna la distancia normalizada al enemigo más cercano en cada dirección (4 direcciones por ejemplo).
      """
      distancias = [1.0] * 8  # derecha, abajo, izquierda, arriba
      step = 5
      x, y = self.rect.center
      direcciones = [0, math.pi/4, math.pi/2, 3*math.pi/4, math.pi, 5*math.pi/4, 3*math.pi/2,7*math.pi/4]

      for i, angle in enumerate(direcciones):
          dx = math.cos(angle)
          dy = math.sin(angle)
          for dist in range(0, max_dist, step):
              test_x = int(x + dx * dist)
              test_y = int(y + dy * dist)
              punto = pygame.Rect(test_x, test_y, 1, 1)
              for enemigo in enemigos:
                  enemigo_rect = pygame.Rect(enemigo.x - enemigo.radio, enemigo.y - enemigo.radio, enemigo.radio * 2, enemigo.radio * 2)
                  if enemigo_rect.colliderect(punto):
                      distancias[i] = dist / max_dist
                      break
              else:
                  continue
              break
      return distancias

    def colisionEnemiga(self, enemigos):
        colision = False
        for i in enemigos:
          temp_rect = pygame.Rect(i.x - i.radio, i.y - i.radio, i.radio * 2,  i.radio * 2)
          if self.rect.colliderect(temp_rect):
            colision = True
        return colision
        
    
    def resetearPosicion(self):
      self.rect.x=230
      self.x=230
      self.rect.y= 339
      self.y=339

    def draw(self, screen):
      screen.blit(self.image, self.rect.topleft)

    def llegarAMeta(self,meta):
      gano = False
      if self.rect.colliderect(meta):
        gano = True
      return gano
    
    def sensor_raycast(self, direction, paredes, max_dist=200):
        """
        Lanza un rayo desde el centro del jugador en una dirección (en radianes)
        y devuelve la distancia a la pared más cercana, hasta max_dist.
        """
        step = 5
        x, y = self.rect.center
        dx = math.cos(direction)
        dy = math.sin(direction)

        for dist in range(0, max_dist, step):
            test_x = int(x + dx * dist)
            test_y = int(y + dy * dist)
            point = pygame.Rect(test_x, test_y, 1, 1)
            if any(pared.rect.colliderect(point) for pared in paredes):
                return dist / max_dist  # normalizado
        return 1.0  # No colisionó en todo el rango

class pared():
  x:int
  y:int
  xf:int
  xy:int
  def __init__ (self, x,y, xf, yf):
    self.rect=pygame.Rect(x,y,xf,yf)
    self.x=x
    self.y=y
    self.xf=xf
    self.yf=yf

class enemigo():
  Vel=7
  direccionO:str
  x: int
  y: int
  x0:int
  y0:int
  direccion0:int
  def __init__(self, x,y,direccionO,direccion):
    self.x0=x
    self.y0=y
    self.x = x
    self.y = y
    self.centro = pygame.Vector2(self.x, self.y)
    self.radio = 12
    self.direccionO = direccionO
    self.direccion=direccion
    self.direccion0=direccion

  
  def mover(self, paredesCreadas):
    dx = dy = 0
    if self.direccionO == "der":
        dx = self.Vel * self.direccion
    elif self.direccionO == "up":
        dy = -self.Vel * self.direccion

    if self.puede_mover_a(dx, dy, paredesCreadas):
        self.x += dx
        self.y += dy
    
    else:
        self.direccion *= -1  # rebotar al detectar colisión
  
  def puede_mover_a(self, dx, dy, paredesCreadas):
    futuro_x = self.x + dx
    futuro_y = self.y + dy

    # crear rectángulo temporal en la futura posición
    temp_rect = pygame.Rect(futuro_x - self.radio, futuro_y - self.radio, self.radio * 2, self.radio * 2)

    # verificar colisiones
    for pared in paredesCreadas:
        if temp_rect.colliderect(pared.rect):
            return False
    return True



  def draw (self,screen,imagen):
    screen.blit(imagen, (self.x-self.radio,self.y-self.radio))

  def resetear(self):
    self.x=self.x0
    self.y=self.y0
    self.direccion=self.direccion0
    self.centro = pygame.Vector2(self.x0, self.y0)

class Game():
  
  #load images
  fuente = pygame.font.SysFont("Arial", 30) 
  texto = fuente.render("GANADOR", True, (255, 255, 255)) 
  BG = (180, 181, 254)
  paredes=[(150, 185, 314, 192),(140,185,147,493),(305,185,311,435),(150,492,400,502),(307,431,347,437),(340,238,347,437),
        (347,233,796,240),(787,185,794,238),(793,181,1040,188),(1048,188,1057,485),(880,485,1047,495),(405,443,851,450),
        (405,443,412,500),(885,245,892,485),(850,245,890,262),(850,245,862,485)]
  checkpoints = [
    pygame.Rect(280, 440, 40, 40),  # después de la salida izquierda
    pygame.Rect(350, 440, 40, 40),
    pygame.Rect(400, 300, 40, 100),  # curva abajo
    pygame.Rect(500, 240, 40, 200),
    pygame.Rect(600, 240, 40, 200),  # final del pasillo bajo
    pygame.Rect(700, 240, 40, 200),  
    pygame.Rect(800, 200, 40, 40),  # curva hacia arriba
    pygame.Rect(900, 200, 40, 40),
    pygame.Rect(1100,200,40,40)  # entrada a la meta
]

  def __init__(self,screen):
    pygame.init()
    self.screen = screen
    #fill background
    #load images
    self.imagen_jugador=pygame.image.load("neat_juego/juego/jugador.png").convert_alpha()
    self.imagen_enemigo= pygame.image.load("neat_juego/juego/enemigo.png").convert_alpha()
    self.mapa = pygame.image.load("neat_juego/juego/mapa.png").convert_alpha()
    
    
    self.player=Jugador(230, 339, self.imagen_jugador)

    self.paredesCreadas = []
    for i in range(0, len(self.paredes)):
      paredaux=(self.paredes[i][0],self.paredes[i][1],(self.paredes[i][2]-self.paredes[i][0]),(self.paredes[i][3]-self.paredes[i][1]))
      final=pared(*paredaux)
      self.paredesCreadas.append(final)

    self.enemigos = []
    for i in range(0,4,1):
      i = enemigo(600,268+(i*50),"der",1*((-1)**(i)))
      self.enemigos.append(i)
      
    self.meta=pygame.Rect(898,199,147,290)
    

  def loop(self, jugadores):
    self.screen.fill(self.BG)
    self.screen.blit(self.mapa, (0, 0))

    for jugador in jugadores:
        jugador.draw(self.screen)

    for enemigo in self.enemigos:
        enemigo.draw(self.screen, self.imagen_enemigo)
        enemigo.mover(self.paredesCreadas)

    if any(j.llegarAMeta(self.meta) for j in jugadores):
        self.screen.blit(self.texto, (100, 100))

    pygame.display.update()

  def reset(self):
    self.player.resetearPosicion()
    for i in self.enemigos:
      i.resetear()
     
