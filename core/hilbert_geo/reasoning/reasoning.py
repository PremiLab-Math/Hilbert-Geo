from hilbert_geo.problem import Problem
from hilbert_geo.core import EquationKiller as EqKiller
from hilbert_geo.parse import parse_predicate_gdl, parse_theorem_gdl, parse_problem_cdl
from hilbert_geo.tools import rough_equal, show_solution
from hilbert_geo.solver import Interactor
import json
import warnings
from copy import deepcopy


class GeometrySolver:
    """The geometric problem solver class encapsulates the complete process of problem handling and solving"""
    
    def __init__(self, predicate_gdl_path, theorem_gdl_path):
        """
        Initialize the solver
        
        """
        self.predicate_gdl = self._load_predicate_gdl(predicate_gdl_path)
        self.theorem_gdl = self._load_theorem_gdl(theorem_gdl_path)
        self.problem = None
        self.solving_history = []
        
    def _load_predicate_gdl(self, path):
        """Load predicate definition"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return parse_predicate_gdl(json.load(f))
        except Exception as e:
            warnings.warn(f"The predicate definition loading failed: {str(e)}")
            return None
    
    def _load_theorem_gdl(self, path):
        """Definition of Loading Theorem"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return parse_theorem_gdl(json.load(f),self.predicate_gdl)
        except Exception as e:
            warnings.warn(f"The definition of the loading theorem failed: {str(e)}")
            return None
    
    def load_problem(self, problem_data):
        """
        Load problem data
        
        """
        try:
            parsed_problem = parse_problem_cdl(problem_data)
            self.problem = Problem()
            self.problem.load_problem_by_fl(
                parsed_predicate_GDL=self.predicate_gdl,  
                parsed_theorem_GDL=self.theorem_gdl,      
                parsed_problem=parsed_problem             
                )
            self.problem._construction_init()  # Execution condition extension
            self.solving_history = [f"The problem has been loaded successfully.: {problem_data.get('problem_id', 'Unknown ID')}"]
            return True
        except Exception as e:
            warnings.warn(f"Loading issue failed: {str(e)}")
            return False
    
    def apply_theorem(self, theorem_name, branch=0):
        """
        Apply the specified theorem
        
        """
        if not self.problem:
            warnings.warn("Please load the question first")
            return False
            
        try:
            branch_key = list(self.theorem_gdl[theorem_name]["body"].keys())[branch]
            interactor = Interactor(self.predicate_gdl, self.theorem_gdl)
            update = Interactor.apply_theorem_by_name_and_branch(
                theorem_name, branch_key
            )
            if update:
                self.solving_history.append(
                    f"Successful application of the theorem: {theorem_name} (Branch {branch})"
                )
                EqKiller.solve_equations(self.problem)  # Solve the equation
                return True
            self.solving_history.append(
                f"应用定理失败: {theorem_name} (分支 {branch})"
            )
            return False
        except Exception as e:
            self.solving_history.append(
                f"Error in applying the theorem: {theorem_name} - {str(e)}"
            )
            return False
    
    def check_goal(self):
        """Check whether the target has been resolved"""
        if not self.problem:
            return False, None
            
        self.problem.check_goal()
        if self.problem.goal.solved:
            return True, self.problem.goal.solved_answer
        return False, None
    
    def solve(self, max_steps=20):
        """
        Automatically solve problems
        
        :param max_steps: Maximum solution steps
        :return: (Whether it has been solved, the answer, and the history of seeking solutions)
        """
        if not self.problem:
            warnings.warn("Please load the question first")
            return False, None, self.solving_history
            
        for step in range(max_steps):
            # Check if it has been resolved
            solved, answer = self.check_goal()
            if solved:
                self.solving_history.append(f"Steps {step + 1}: The goal has been solved. The answer: {answer}")
                return True, answer, self.solving_history
            
            # Try to apply all available theorems
            theorem_applied = False
            for theorem_name in self.theorem_gdl:
                    
                # Try all branches
                for branch_idx, branch_key in enumerate(self.theorem_gdl[theorem_name]["body"].keys()):
                    if self.apply_theorem(theorem_name, branch_idx):
                        theorem_applied = True
                        break  # After the application is successful, continue to check the target
                if theorem_applied:
                    break
            
            if not theorem_applied:
                self.solving_history.append(f"Step {step + 1}: There are no available theorems to apply, and the solution is terminated")
                break
        
        # Final inspection
        solved, answer = self.check_goal()
        return solved, answer, self.solving_history
    
    def show_solution(self):
        """Details of the solution process"""
        if not self.problem:
            warnings.warn("Please load the question first")
            return
        show_solution(self.problem)
    
    def get_history(self):
        """Get history"""
        return self.solving_history
    
    def copy(self):
        """Create a copy of the solver (for branch exploration)"""
        new_solver = GeometrySolver(None, None)
        new_solver.predicate_gdl = deepcopy(self.predicate_gdl)
        new_solver.theorem_gdl = deepcopy(self.theorem_gdl)
        new_solver.problem = deepcopy(self.problem)
        new_solver.solving_history = deepcopy(self.solving_history)
        return new_solver
