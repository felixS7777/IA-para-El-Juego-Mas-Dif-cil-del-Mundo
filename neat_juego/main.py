# main.py (modificado para correr 50 jugadores simultáneos)
import pygame
import neat
import math
import os
from juego import Game, Jugador

contador: int

class juegoMultiple:
    def __init__(self, genomes, config,screen):
        self.game = Game(screen)
        self.checkpoints = self.game.checkpoints
        self.players = []
        self.nets = []
        self.genomes = []
        self.checkpoint_indices = []

        for genome_id, genome in genomes:
            genome.fitness = 0
            player = Jugador(230, 339, self.game.imagen_jugador)
            self.players.append(player)
            net = neat.nn.FeedForwardNetwork.create(genome, config)
            self.nets.append(net)
            self.genomes.append(genome)
            self.checkpoint_indices.append(0)

        self.prev_dists = []
        for i, player in enumerate(self.players):
            checkpoint = self.get_checkpoint_actual(i)
            cx = (checkpoint.left + checkpoint.right) / 2
            cy = (checkpoint.top + checkpoint.bottom) / 2
            dist = math.hypot(cx - player.x, cy - player.y)
            self.prev_dists.append(dist)
        
        self.stagnation_frames = [0 for _ in self.players]
        self.prev_positions = [(player.x, player.y) for player in self.players]
        self.alive = [True for _ in self.players]


    def get_checkpoint_actual(self, i):
        if self.checkpoint_indices[i] < len(self.checkpoints):
            return self.checkpoints[self.checkpoint_indices[i]]
        return None

    def update(self):
        global frame_limit
        global frame_count
        global contador
        for i, player in enumerate(self.players):
            if not self.alive[i]:
                continue
            inputs = [
                player.x / 1200,
                player.y / 678]
                

            checkpoint = self.get_checkpoint_actual(i)

            esta_en_inicio = 1.0 if player.x <= 300 else 0.0
            inputs.append(esta_en_inicio)

            inputs.extend(player.sensor_enemigos(self.game.enemigos))

            ray_directions = [
                0,                   # derecha
                math.pi / 2,         # abajo
                math.pi,             # izquierda
                3 * math.pi / 2,     # arriba
            ]

            dx_goal = (((checkpoint.right+checkpoint.left)/2) - player.x) / 1200
            dy_goal = (((checkpoint.bottom+checkpoint.top)/2)- player.y) / 678
            inputs.extend([dx_goal, dy_goal])

            for angle in ray_directions:
                dist = player.sensor_raycast(angle, self.game.paredesCreadas)
                inputs.append(dist)

            output = self.nets[i].activate(inputs)
            player.mover_desde_ia(output, self.game.paredesCreadas)
            
            if checkpoint and player.rect.colliderect(checkpoint):
                if self.alive[i]:
                    self.checkpoint_indices[i] += 1
                    self.genomes[i].fitness += 300 * self.checkpoint_indices[i]

            if player.colisionEnemiga(self.game.enemigos):
                if self.alive[i]:
                    self.genomes[i].fitness -= 4750
                    contador -= 1
                    self.alive[i] = False
                    

            distancia = math.hypot(((checkpoint.right+checkpoint.left)/2) - player.x, ((checkpoint.bottom+checkpoint.top)/2) - player.y)

            prev_dist = self.prev_dists[i]
            curr_dist = distancia
            delta = prev_dist - curr_dist  # si se acercó al checkpoint, esto es positivo

            if delta > 0:
                self.genomes[i].fitness += delta * 30  # premiar avance real
            else:
                self.genomes[i].fitness += delta * 5  # castigar retroceso leve
            self.prev_dists[i] = curr_dist
                        

            if frame_count >= 90 and player.x<=300:
                self.genomes[i].fitness -=75

            if frame_count >= 140 and (player.y >= 430 or player.x<=300):
                self.genomes[i].fitness -=50

            if frame_count == 200 and (player.y >= 430 or player.x<=300):
                self.genomes[i].fitness -=5500
                contador -= 1
                self.alive[i] = False
            

            if (player.y <= 440 and player.x>= 350) and self.alive[i]:
                self.genomes[i].fitness += 75

            if abs(player.x - self.prev_positions[i][0]) < 1 and abs(player.y - self.prev_positions[i][1]) < 1:
                self.stagnation_frames[i] += 1
            else:
                self.stagnation_frames[i] = 0
                self.prev_positions[i] = (player.x, player.y)

            if self.stagnation_frames[i] > 60:  # más de 1 segundo sin 
                if self.alive[i]:
                    self.genomes[i].fitness -= 500

            if self.stagnation_frames[i] > 60 and frame_count >= 60 and frame_count <= 70:
                if self.alive[i]:
                    self.genomes[i].fitness -= 7000
                    self.alive[i] = False
                    contador -= 1

            if self.checkpoint_indices[i] == 6:
                self.genomes[i].fitness += (600-player.y)*0.1

            if player.choco_con_pared:
                if self.alive[i]:
                    self.genomes[i].fitness -= 75
                
            if player.y<=180:
                self.genomes[i].fitness -= 100000
                self.alive[i] = False
                contador -= 1

            if self.alive[i] and player.choco_con_pared and frame_count < 30:
                self.genomes[i].fitness -= 100  # penalizar fuertemente a los que ya arrancan chocando

            if player.llegarAMeta(self.game.meta):
                if self.alive[i]:
                    self.genomes[i].fitness += 100000

    def draw(self):
        self.game.screen.fill(self.game.BG)
        self.game.screen.blit(self.game.mapa, (0, 0))

        for i,player in enumerate(self.players):
            if not self.alive[i]:
                continue
            player.draw(self.game.screen)

        for enemigo in self.game.enemigos:
            enemigo.draw(self.game.screen, self.game.imagen_enemigo)
            enemigo.mover(self.game.paredesCreadas)

        global generation_counter

        fuente = pygame.font.SysFont("Arial", 30) 
        texto = fuente.render(("generacion: " + str(generation_counter)), True, (255,255,255)) 
        self.game.screen.blit(texto, (0, 0))
        pasos = fuente.render("pasos: " + str(100 + 50 * (generation_counter // 500)), True, (255,255,255))
        self.game.screen.blit(pasos, (0, 50))

        global contador

        vivos = fuente.render("jugadores vivos: " + str(contador), True, (255,255,255))
        self.game.screen.blit(vivos, (0, 100))

        
        pygame.display.update()

generation_counter = 2757

def eval_genomes(genomes, config,screen):
    global frame_limit
    global frame_count
    global contador
    global generation_counter
    generation_counter +=1
    clock = pygame.time.Clock()
    jm = juegoMultiple(genomes, config,screen)
    run = True

    
    frame_limit = 100 + 50 * (generation_counter // 500)
    
    frame_count = 0
    contador = len(genomes)
    while run and frame_count < frame_limit:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        jm.update()
        jm.draw()
        frame_count += 1
    


def run_neat(config):
    pygame.init()
    SCREEN_WIDTH = 1200
    SCREEN_HEIGHT = 678
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("juego mas dificil del mundo")
    def eval_genomes_anidado (genomes,config):
        eval_genomes(genomes,config,screen)
    p= neat.Checkpointer.restore_checkpoint("neat-checkpoint-2758")
    p.config.fitness_threshold = 100000
    #p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(1))
    winner = p.run(eval_genomes_anidado)



if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config.txt")
    config = neat.Config(neat.DefaultGenome,
                         neat.DefaultReproduction,
                         neat.DefaultSpeciesSet,
                         neat.DefaultStagnation,
                         config_path)
    run_neat(config)
