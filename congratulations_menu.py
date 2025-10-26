import pygame
def run_congratulations(screen, level_completed=1, coins_collected=0, total_coins=0, new_avatar_unlocked=None):
	"""
	Display a simple congratulations screen and wait for user input.
	Returns a dict with 'action' key: 'next_level', 'retry', 'home', or 'quit'.
	"""
	font = pygame.font.SysFont("arial", 32)
	small_font = pygame.font.SysFont("arial", 20)
	clock = pygame.time.Clock()
	running = True
	action = None
	while running:
		screen.fill((30, 30, 60))
		title = font.render(f"Congratulations!", True, (255, 255, 0))
		level_text = small_font.render(f"Level {level_completed} completed!", True, (200, 255, 200))
		coins_text = small_font.render(f"Coins collected: {coins_collected}", True, (255, 255, 255))
		total_text = small_font.render(f"Total coins: {total_coins}", True, (255, 255, 255))
		screen.blit(title, (100, 80))
		screen.blit(level_text, (100, 140))
		screen.blit(coins_text, (100, 180))
		screen.blit(total_text, (100, 210))
		y = 250
		if new_avatar_unlocked:
			unlock_text = small_font.render(f"New avatar unlocked: {new_avatar_unlocked}", True, (255, 215, 0))
			screen.blit(unlock_text, (100, y))
			y += 30
		# Instructions
		instr1 = small_font.render("SPACE: Next Level", True, (180, 255, 180))
		instr2 = small_font.render("R: Retry Level", True, (180, 180, 255))
		instr3 = small_font.render("H: Home Menu", True, (255, 180, 180))
		instr4 = small_font.render("ESC: Quit", True, (255, 180, 180))
		screen.blit(instr1, (100, y + 20))
		screen.blit(instr2, (100, y + 50))
		screen.blit(instr3, (100, y + 80))
		screen.blit(instr4, (100, y + 110))
		pygame.display.flip()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				action = 'quit'
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_SPACE:
					action = 'next_level'
					running = False
				elif event.key == pygame.K_r:
					action = 'retry'
					running = False
				elif event.key == pygame.K_h:
					action = 'home'
					running = False
				elif event.key == pygame.K_ESCAPE:
					action = 'quit'
					running = False
		clock.tick(30)
	return {'action': action}
