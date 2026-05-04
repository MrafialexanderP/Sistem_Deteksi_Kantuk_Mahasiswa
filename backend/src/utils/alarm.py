import pygame

class Alarm:
    def __init__(self, sound_path):
        pygame.mixer.init()
        self.sound = pygame.mixer.Sound(sound_path)
        self.is_playing = False

    def play(self):
        if not self.is_playing:
            self.sound.play(-1) 
            self.is_playing = True

    def stop(self):
        if self.is_playing:
            self.sound.stop()
            self.is_playing = False