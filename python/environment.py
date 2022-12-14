import sys

# Path to pddlgym
sys.path.append('../../pddlgym')

import pddlgym
from gym import error
from pddlgym.core import InvalidAction
import imageio
from torchvision.transforms.functional import to_tensor

import matplotlib; matplotlib.use('agg')

class Environment(object):
    '''
    Wrapper for pddlgym environment.
    '''

    def __init__(self, 
                env_name="PDDLEnvSimple-v0",
                problem_index=0):
        '''
        Initializes pddlgym environment.

        env_name: pddlgym style environment name string.
        problem_index: pddl problem file index
        returns: nothing.
        '''
        self.env = None

        while not self.env:
            try:
                # Create environmet
                self.env = pddlgym.make(env_name, raise_error_on_invalid_action=True)
                # self.env.fix_problem_index(3)

            except error.NameNotFound as e:
                print(e)
                # Ask user to input correct environment name
                env_name = input("Please input correct environment name: ")

        # Variable to track timesteps
        self.timestep = None
        self.location = None
        self.reset()
        
        
    def render(self):
        '''
        Wrapper for render function for gym environment.
        returns: image array of environment at current timestep.
        '''
        return self.env.render()

    def save_render(self, 
                    img, 
                    prefix="results/"):
        '''
        Wrapper to save rendered image of environment for current timestep.
        img: image array of render.
        prefex: directory to save render image file
        '''

        imageio.imsave(f'{prefix}{str(self.timestep).zfill(3)}.png', img)
    
    def get_cache_location(self, obs):
        """
        Gets the ground truth location of the agent for debugging purposes
        """
        if obs is not None:
            for lit in obs.literals:
                if lit.predicate.name == "at" and not lit.predicate.is_negative:
                    self.location = lit.variables[0].split(":")[0]
                    return self.location
        return self.location

    def step(self, 
            action):
        '''
        Wrapper for gym step function.
        '''

        # Try executing the actions
        success = None 
        done = False
        
        obs = None
        prev_loc = self.location
        try:
            obs, _, done, _ = self.env.step(action)
            self.timestep += 1

            success = True

        # Action fails
        except InvalidAction as e:

            success = False

        img = self.render()
        self.save_render(img)

        info = {
            "result": success, 
            "location": {
                "before": prev_loc,
                "after": self.get_cache_location(obs)
            }
        }

        return self.rendering_to_obs(img), self.timestep, done, info
    
    def rendering_to_obs(self, rendering):
        '''
        Converts rendering to observation.
        rendering: image array of rendered environment.
        returns: observation array.
        '''
        return to_tensor(rendering[:, :, :3])


    def reset(self, problem_index=None):
        '''
        Wrapper for gym reset function. Fixes problem index for pddl problem file.
        '''

        # Set timesteps to 0
        self.timestep = 0

        # Reset environment
        if problem_index is not None:
            self.env.fix_problem_index(problem_index)
        obs, info = self.env.reset()
        # re-arrange order of axis is needed for pytorch
        img = self.render()
        # store the ground truth location of the agent, for tesing purposes
        self.get_cache_location(obs)
        return self.rendering_to_obs(img), info
