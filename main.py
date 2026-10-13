import pygame
import random
import sys
import math
import time
import asyncio    

pygame.init()
WIDTH = 500
HEIGHT= 500
#initialization stuff
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroids !")
clock = pygame.time.Clock()

async def main():

    #variabless
    font1 = pygame.font.Font(None, 18)
    font2 = pygame.font.Font(None, 30)
    FPS = 60
    MISSILE_SPEED = 20
    SHIP_MAX_SPEED = 5
    SHIP_ROTATION_SPEED = 10
    THRUST = 0.5
    DRAG = 0.99
    SCORE = 0
    DETECTION_RANGE = 250
    FOV_THRESHOLD = 0.7
    SHIP_HEALTH = 200
    ENEMY_HEALTH = 100
    GOAL = 20

    # classes :)
    class Asteroid:
        # variable initialized
        def __init__(self, radius, color):
            self.radius = radius
            self.color = color
            self.asteroidVector = pygame.math.Vector2(random.randint(random.randint(radius + 20, WIDTH / 4), random.randint(WIDTH * 3/4, WIDTH - radius)), random.randint(random.randint(radius + 20, HEIGHT /4), random.randint(HEIGHT * 3/4, HEIGHT - radius)))
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.0, 2.5)
            self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed

        def update(self):
            self.asteroidVector += self.velocity
            
            if self.asteroidVector.x > WIDTH + self.radius:
                self.asteroidVector.x = -self.radius

            if self.asteroidVector.x < -self.radius:
                self.asteroidVector.x = WIDTH + self.radius

            if self.asteroidVector.y > HEIGHT + self.radius:
                self.asteroidVector.y = -self.radius

            if self.asteroidVector.y < -self.radius:
                self.asteroidVector.y = HEIGHT + self.radius

        def asteroid_asteroidCollision(self, other):
            if self.asteroidVector.distance_to(other.asteroidVector) < self.radius + other.radius + 1:
                temp = self.velocity
                self.velocity = other.velocity
                other.velocity = temp * -1

        #rendering
        def draw(self):
            pygame.draw.circle(screen, self.color, self.asteroidVector, self.radius)
    class SpaceShip:
        #initializing
        def __init__(self):
            self.ShipVector = pygame.math.Vector2(WIDTH / 2, HEIGHT / 2)
            self.color = (0, 255, 0)
            self.angle = 90
            self.velocity = pygame.math.Vector2(0, 0)
            self.acceleration = pygame.math.Vector2(0, 0)

        def getForwardVector(self):
            radian = math.radians(self.angle)
            forwardVector = pygame.math.Vector2(math.cos(radian), -math.sin(radian))
            return forwardVector

        
        def update(self):
            self.isThrusting = False
            self.acceleration = pygame.Vector2(0, 0)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.angle += SHIP_ROTATION_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.angle -= SHIP_ROTATION_SPEED

            forward = self.getForwardVector()
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.acceleration = forward * THRUST
                self.isThrusting = True

            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.acceleration = -forward * THRUST
                self.isThrusting = True

            self.velocity += self.acceleration
            self.velocity *= DRAG
            if self.velocity.length() > SHIP_MAX_SPEED:
                self.velocity.scale_to_length(SHIP_MAX_SPEED)
            self.ShipVector += self.velocity
            
            if self.ShipVector.x > WIDTH:
                self.ShipVector.x = 0

            if self.ShipVector.x < 0:
                self.ShipVector.x = WIDTH

            if self.ShipVector.y > HEIGHT:
                self.ShipVector.y = 0

            if self.ShipVector.y < 0:
                self.ShipVector.y = HEIGHT

        def drawThrust(self):
            if self.isThrusting:
                backPos = self.ShipVector - self.forward * 18
                pygame.draw.circle(screen, (255, 255, 0), backPos, 5)

        def draw(self):
            self.forward = self.getForwardVector()
            left = self.forward.rotate(140)
            right = self.forward.rotate(-140)
            points = [(self.ShipVector + self.forward * 22), (self.ShipVector + left * 17), (self.ShipVector + right * 17)]
            pygame.draw.polygon(screen, self.color, points, 3)
            pygame.draw.polygon(screen, (0, 255, 0), points, 2)
        def drawVectorLine(self):
            endPoint = self.ShipVector + self.getForwardVector() * 60
            pygame.draw.line(screen, (255, 0, 0), self.ShipVector, endPoint, 5)
    class Missile:
        #initialization
        def __init__(self, start, direction):
            self.MissilePosition = pygame.math.Vector2(start)
            self.radius = 5
            if direction.length() != 0:
                direction = direction.normalize()
            self.velocity = direction * MISSILE_SPEED

        def update(self):
            self.MissilePosition += self.velocity

        def draw(self):
            pygame.draw.circle(screen, (255, 255, 0), self.MissilePosition, self.radius)

        def outOfBounds(self):
            return (self.MissilePosition.x < 0
                    or self.MissilePosition.x > WIDTH
                    or self.MissilePosition.y < 0
                    or self.MissilePosition.y > HEIGHT)
    class EnemySpaceShip:
        def __init__(self):
            self.EnemyVector = pygame.math.Vector2(WIDTH / random.randint(2,5), HEIGHT / random.randint(2,5))
            self.EnemyAngle = 0
            self.forward = pygame.math.Vector2(1, 0)
            self.shootingTimer = 0
            self.missiles = []
            self.radius = 10

        def detection(self, ship):
            playerToEnemy = ship.ShipVector - self.EnemyVector
            range = playerToEnemy.length()
            if range > 0:
                playerToEnemy = playerToEnemy.normalize()
            radians = math.radians(self.EnemyAngle)
            self.forward = pygame.math.Vector2(math.cos(radians), -math.sin(radians))
            proximity = self.forward.dot(playerToEnemy)
            if range < DETECTION_RANGE and proximity > FOV_THRESHOLD:
                return True
            return False

        def movementMode(self, ship):
            if self.detection(ship):
                direction = ship.ShipVector - self.EnemyVector
                if direction.length() > 0:
                    direction = direction.normalize()
                self.EnemyVector += direction * 3
            else:
                self.EnemyVector += pygame.math.Vector2(1, 0)


        def update(self, ship):
            self.EnemyAngle += 1
            
            if self.shootingTimer > 0:
                self.shootingTimer -= 1

            if self.detection(ship):
                if self.shootingTimer == 0:
                    direction = ship.ShipVector - self.EnemyVector
                    if direction.length() > 0:
                        direction = direction.normalize()
                        missile = Missile(self.EnemyVector, direction)
                        self.missiles.append(missile)
                        self.shootingTimer = 10
            
            if self.EnemyVector.x > WIDTH:
                self.EnemyVector.x = 0

            if self.EnemyVector.x < 0:
                self.EnemyVector.x = WIDTH

            if self.EnemyVector.y > HEIGHT:
                self.EnemyVector.y = 0

            if self.EnemyVector.y < 0:
                self.EnemyVector.y = HEIGHT

        def draw(self):
            pygame.draw.circle(screen, (10, 10, 10), self.EnemyVector, DETECTION_RANGE, 1)
            pygame.draw.circle(screen, (255, 0, 0), self.EnemyVector, self.radius, 3)
            pygame.draw.line(screen, (240, 0, 0), self.EnemyVector, self.EnemyVector + self.forward * 100, 3)

    #Missile Collisions
    def Missile_AsteroidCollision(missile, asteroid):
        distance = missile.MissilePosition.distance_to(asteroid.asteroidVector)
        return distance < missile.radius + asteroid.radius
    def Missile_ShipCollision(missile, ship):
        distance = missile.MissilePosition.distance_to(ship.ShipVector)
        return distance < missile.radius + 20
    def Missile_EnemyCollision(missile, enemy):
        distance = missile.MissilePosition.distance_to(enemy.EnemyVector)
        return distance < missile.radius + enemy.radius 
    #Asteroid Ship Collision
    def asteroid_shipCollosion(asteroid, ship):
        distance = asteroid.asteroidVector.distance_to(ship.ShipVector)
        return distance < asteroid.radius + 10
    
    #GAME OBJECTS
    ##Asteroid
    asteroids = []
    for a in range(10):
        rgb = random.randint(50, 255)
        asteroid = Asteroid(random.randint(5, 10), (rgb, rgb, rgb))
        asteroids.append(asteroid)
    ##Center pt
    pygame.draw.circle(screen, (0, 255, 0), (WIDTH /2, HEIGHT / 2), 3)
    #Ship
    ship = SpaceShip()
    #Missiles
    player_missiles = []
    #enemy
    enemy = EnemySpaceShip()

    #game running
    running = True
    enemyDefeated = False
    playerDefeated = False
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        #missile creation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    missile = Missile(ship.ShipVector, ship.getForwardVector())
                    player_missiles.append(missile)

        #Game Object Updates
        for asteroid in asteroids:
            asteroid.update()
        for missile in player_missiles:
            missile.update()
        if ENEMY_HEALTH > 0:
            enemy.movementMode(ship)
            #enemy updates
            if enemy.detection(ship) == True:
                e_Mode = "ATTACK"
                e_Text = (255, 0, 0)
                enemyToPlayer = ship.ShipVector - enemy.EnemyVector
                if enemyToPlayer.length() > 0:
                    enemyToPlayer = enemyToPlayer.normalize()
                    
                missile_velocity = (enemyToPlayer * MISSILE_SPEED)
            if enemy.detection(ship) == False:
                e_Mode = "PATROL"
                e_Text = (0, 255, 0)

            for missile in enemy.missiles:
                missile.update()
            enemy.update(ship)
        player_missiles = [missile for missile in player_missiles if not missile.outOfBounds()]
        ship.update()

        #collision
        for i in range (len(asteroids)):
                for j in range (i + 1, len(asteroids)):
                    asteroids[i].asteroid_asteroidCollision(asteroids[j])

        for missile in player_missiles:
            for asteroid in asteroids:
                if Missile_AsteroidCollision(missile, asteroid):
                    if missile in player_missiles:
                            player_missiles.remove(missile)
                    if asteroid in asteroids:
                            asteroids.remove(asteroid)

                    asteroids.append(Asteroid(random.randint(5, 10), (rgb, rgb, rgb)))
                    SCORE += 1
                    break
                if Missile_EnemyCollision(missile, enemy):
                    if missile in player_missiles:
                        player_missiles.remove(missile)
                    ENEMY_HEALTH -= 10

        for missile in enemy.missiles:
            if Missile_ShipCollision(missile, ship):
                if missile in enemy.missiles:
                    enemy.missiles.remove(missile)
                SHIP_HEALTH -= 10
        for asteroid in asteroids:
            if asteroid_shipCollosion(asteroid, ship):
                if asteroid in asteroids:
                    asteroids.remove(asteroid)
                
                asteroids.append(Asteroid(random.randint(5, 10), (rgb, rgb, rgb)))
                SHIP_HEALTH -= 1

        if ENEMY_HEALTH <= 0:
            enemyDefeated = True
            e_Mode = "DEAD!!!!!!"
            ENEMY_HEALTH = 0
            e_Text = (255, 0, 0)

        if SHIP_HEALTH <= 0:
            playerDefeated = True
            ded = "Ship has been destroyed!"
            SHIP_HEALTH = 0

        #Game Conditionals
        if playerDefeated == True:
            screen.blit(font2.render(ded, True, (255, 0, 0)), (WIDTH / 2 - 150, HEIGHT / 2))
            pygame.display.flip()
            await asyncio.sleep(2)
            running = False
        if enemyDefeated and SCORE >= GOAL:
            gaolllll = "GOOD GAME !!!!"
            screen.blit(font2.render(gaolllll, True, (0, 255, 0)), (WIDTH / 2 - 75, HEIGHT / 2))
            pygame.display.flip()
            await asyncio.sleep(2)
            running = False
        if enemyDefeated and SCORE >= GOAL and SHIP_HEALTH == 200:
            gaolllll = "Wowzers ur good :D"
            screen.blit(font2.render(gaolllll, True, (0, 255, 0)), (WIDTH / 2 - 75, HEIGHT / 2))
            pygame.display.flip()
            await asyncio.sleep(2)
            running = False

        #Rendering
        screen.fill((0, 0, 0))
        ship.draw()
        shipText = "You"
        screen.blit(font1.render(shipText, True, (0, 255, 0)), (ship.ShipVector.x, ship.ShipVector.y + 20))
        if enemyDefeated != True:
            enemy.draw()
            enemytext = "Enemy"
            screen.blit(font1.render(enemytext, True, (255, 0, 0)), (enemy.EnemyVector.x, enemy.EnemyVector.y + 20))
        for asteroid in asteroids:
            asteroid.draw()
        for missile in player_missiles:
            missile.draw()
        for missile in enemy.missiles:
            missile.draw()

        #Text making
        ShootingInstruction = "*Click 'E' to fire missile"
        AngleInstruction = "*Click L/R Arrow keys to Position Ship"
        ShipCoords = f"Ship Coords: ({ship.ShipVector.x:.2f}, {ship.ShipVector.y:.2f})"
        ShipAngle = f"Ship Angle: {ship.angle % 360:.0f} degrees"
        ScoreText = f"Asteroids Hit: {SCORE} out of {GOAL}"
        EnemyDetection = f"Enemy Mode: {e_Mode}"
        PlayerHealth = f"Player Health: {SHIP_HEALTH}"
        EnemyHealth = f"Enemy Health: {ENEMY_HEALTH}"
        Goal = f"Shoot down {GOAL} asteroids + kill the enemy to win!"

        #Text Rendering
        yCordText = 20
        screen.blit(font1.render(ShootingInstruction, True, (255, 255, 255)), (20, yCordText))
        screen.blit(font1.render(PlayerHealth, True, (255, 255, 255)), (WIDTH - 125, yCordText))
        screen.blit(font1.render(AngleInstruction, True, (255, 255, 255)), (20, yCordText + 25))
        screen.blit(font1.render(EnemyHealth, True, (255, 255, 255)), (WIDTH - 125, yCordText + 25))
        screen.blit(font1.render(ShipCoords, True, (0, 0, 255)), (20, yCordText + 50))
        screen.blit(font1.render(ShipAngle, True, (0, 0, 255)), (20, yCordText + 75))
        screen.blit(font1.render(ScoreText, True, (255, 255, 255)), (20, yCordText + 100))
        screen.blit(font1.render(EnemyDetection, True, e_Text), (20, yCordText + 125))
        screen.blit(font1.render(Goal, True, (255, 255, 255)), (20, HEIGHT - 35))

        pygame.display.flip()
        await asyncio.sleep(0)
    pygame.quit()

asyncio.run(main())