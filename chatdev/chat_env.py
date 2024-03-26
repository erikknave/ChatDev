# Document this file

import os
import re
import shutil
import signal
import subprocess
import time
from typing import Dict

import openai
import requests

from chatdev.codes import Codes
from chatdev.documents import Documents
from chatdev.roster import Roster
from chatdev.utils import log_and_print_online


"""
A configuration class for Chat Environment settings.

Attributes:
    clear_structure (bool): Flag to clear the directory structure.
    brainstorming (bool): Flag to enable brainstorming mode.
    gui_design (bool): Flag to enable GUI design mode.
    git_management (bool): Flag to enable git management features.
"""
class ChatEnvConfig:
    def __init__(self, clear_structure, brainstorming, gui_design, git_management):
        self.clear_structure = clear_structure
        self.brainstorming = brainstorming
        self.gui_design = gui_design
        self.git_management = git_management

    def __str__(self):
        string = ""
        string += "ChatEnvConfig.clear_structure: {}\n".format(self.clear_structure)
        string += "ChatEnvConfig.brainstorming: {}\n".format(self.brainstorming)
        return string


"""
Main class for managing the chat environment.

This class handles the setup and management of the chat environment, including managing codes, documents, images, and executing commands within the environment.

Attributes:
    config (ChatEnvConfig): Configuration settings for the chat environment.
    roster (Roster): The roster of agents participating in the chat environment.
    codes (Codes): Container for code snippets and their management.
    proposed_images (Dict[str, str]): Dictionary of proposed images by filename.
    incorporated_images (Dict[str, str]): Dictionary of images that have been incorporated into the environment.
    requirements (Documents): Container for requirement documents.
    manuals (Documents): Container for manual documents.
    env_dict (dict): Dictionary containing environment variables.
"""
class ChatEnv:
    def __init__(self, chat_env_config: ChatEnvConfig):
        self.config = chat_env_config
        self.roster: Roster = Roster()
        self.codes: Codes = Codes()
        self.proposed_images: Dict[str, str] = {}
        self.incorporated_images: Dict[str, str] = {}
        self.requirements: Documents = Documents()
        self.manuals: Documents = Documents()
        self.env_dict = {
            "directory": "",
            "task_prompt": "",
            "modality": "",
            "ideas": "",
            "language": "",
            "review_comments": "",
            "error_summary": "",
            "test_reports": "",
        }

    @staticmethod
    def fix_module_not_found_error(test_reports):
        """
        Attempts to fix a ModuleNotFoundError by installing the missing module.

        Args:
            test_reports (str): The output from test reports which may contain error messages.
        """
        if "ModuleNotFoundError" in test_reports:
            for match in re.finditer(
                r"No module named '(\S+)'", test_reports, re.DOTALL
            ):
                module = match.group(1)
                subprocess.Popen("pip install {}".format(module), shell=True).wait()
                log_and_print_online(
                    "**[CMD Execute]**\n\n[CMD] pip install {}".format(module)
                )

    def set_directory(self, directory):
        """
        Sets the working directory for the chat environment and manages directory structure based on configuration.

        Args:
            directory (str): The path to the working directory.
        """
        assert len(self.env_dict["directory"]) == 0
        self.env_dict["directory"] = directory
        self.codes.directory = directory
        self.requirements.directory = directory
        self.manuals.directory = directory

        if (
            os.path.exists(self.env_dict["directory"])
            and len(os.listdir(directory)) > 0
        ):
            new_directory = "{}.{}".format(
                directory, time.strftime("%Y%m%d%H%M%S", time.localtime())
            )
            shutil.copytree(directory, new_directory)
            print("{} Copied to {}".format(directory, new_directory))
        if self.config.clear_structure:
            if os.path.exists(self.env_dict["directory"]):
                shutil.rmtree(self.env_dict["directory"])
                os.mkdir(self.env_dict["directory"])
                print("{} Created".format(directory))
            else:
                os.mkdir(self.env_dict["directory"])

    def exist_bugs(self) -> tuple[bool, str]:
        """
        Checks if there are any bugs in the software by running it.

        Returns:
            tuple[bool, str]: A tuple containing a boolean indicating if bugs exist and a string with the error message or success information.
        """
        directory = self.env_dict["directory"]

        success_info = "The software run successfully without errors."
        try:
            command = "cd {}; ls -l; python3 main.py;".format(directory)
            process = subprocess.Popen(
                command,
                shell=True,
                preexec_fn=os.setsid,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(3)
            return_code = process.returncode
            # Check if the software is still running
            if process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            if return_code == 0:
                return False, success_info
            else:
                error_output = process.stderr.read().decode("utf-8")
                if error_output:
                    if "Traceback".lower() in error_output.lower():
                        errs = error_output.replace(directory + "/", "")
                        return True, errs
                else:
                    return False, success_info
        except subprocess.CalledProcessError as e:
            return True, f"Error: {e}"
        except Exception as ex:
            return True, f"An error occurred: {ex}"

        return False, success_info

    def recruit(self, agent_name: str):
        """
        Recruits a new agent into the chat environment.

        Args:
            agent_name (str): The name of the agent to recruit.
        """
        self.roster._recruit(agent_name)

    def exist_employee(self, agent_name: str) -> bool:
        """
        Checks if an agent exists in the roster.

        Args:
            agent_name (str): The name of the agent to check.

        Returns:
            bool: True if the agent exists, False otherwise.
        """
        return self.roster._exist_employee(agent_name)

    def print_employees(self):
        """
        Prints the names of all agents in the roster.
        """
        self.roster._print_employees()

    def update_codes(self, generated_content):
        """
        Updates the codes in the environment with the generated content.

        Args:
            generated_content (str): The content to update the codes with.
        """
        self.codes._update_codes(generated_content)

    def rewrite_codes(self) -> None:
        """
        Rewrites the codes in the environment based on the current configuration.
        """
        self.codes._rewrite_codes(self.config.git_management)

    def get_codes(self) -> str:
        """
        Retrieves the current codes from the environment.

        Returns:
            str: The current codes as a string.
        """
        return self.codes._get_codes()

    def _load_from_hardware(self, directory) -> None:
        """
        Loads codes from hardware into the environment.

        Args:
            directory (str): The directory from which to load the codes.
        """
        self.codes._load_from_hardware(directory)

    def _update_requirements(self, generated_content):
        """
        Updates the requirements documents with the generated content.

        Args:
            generated_content (str): The content to update the requirements with.
        """
        self.requirements._update_docs(generated_content)

    def rewrite_requirements(self):
        """
        Rewrites the requirements documents based on the current content.
        """
        self.requirements._rewrite_docs()

    def get_requirements(self) -> str:
        """
        Retrieves the current requirements documents from the environment.

        Returns:
            str: The current requirements documents as a string.
        """
        return self.requirements._get_docs()

    def _update_manuals(self, generated_content):
        """
        Updates the manuals with the generated content.

        Args:
            generated_content (str): The content to update the manuals with.
        """
        self.manuals._update_docs(
            generated_content, parse=False, predifined_filename="manual.md"
        )

    def rewrite_manuals(self):
        """
        Rewrites the manuals based on the current content.
        """
        self.manuals._rewrite_docs()

    def write_meta(self) -> None:
        """
        Writes metadata about the current state of the chat environment to a file.
        """
        directory = self.env_dict["directory"]

        if not os.path.exists(directory):
            os.mkdir(directory)
            print("{} Created.".format(directory))

        meta_filename = "meta.txt"
        with open(
            os.path.join(directory, meta_filename), "w", encoding="utf-8"
        ) as writer:
            writer.write("{}:\n{}\n\n".format("Task", self.env_dict["task_prompt"]))
            writer.write("{}:\n{}\n\n".format("Config", self.config.__str__()))
            writer.write("{}:\n{}\n\n".format("Roster", ", ".join(self.roster.agents)))
            writer.write("{}:\n{}\n\n".format("Modality", self.env_dict["modality"]))
            writer.write("{}:\n{}\n\n".format("Ideas", self.env_dict["ideas"]))
            writer.write("{}:\n{}\n\n".format("Language", self.env_dict["language"]))
            writer.write("{}:\n{}\n\n".format("Code_Version", self.codes.version))
            writer.write(
                "{}:\n{}\n\n".format(
                    "Proposed_images", len(self.proposed_images.keys())
                )
            )
            writer.write(
                "{}:\n{}\n\n".format(
                    "Incorporated_images", len(self.incorporated_images.keys())
                )
            )
        print(os.path.join(directory, meta_filename), "Wrote")

    def generate_images_from_codes(self):
        """
        Generates images based on the codes in the environment and updates the incorporated images.
        """
        def download(img_url, file_name):
            r = requests.get(img_url)
            filepath = os.path.join(self.env_dict["directory"], file_name)
            if os.path.exists(filepath):
                os.remove(filepath)
            with open(filepath, "wb") as f:
                f.write(r.content)
                print("{} Downloaded".format(filepath))

        regex = r"(\w+.png)"
        joined_codes = self.get_codes()
        matches = re.finditer(regex, joined_codes, re.DOTALL)
        # matched_images = {}
        for match in matches:
            filename = match.group(1).strip()
            if filename in self.proposed_images.keys():
                self.incorporated_images[filename] = self.proposed_images[filename]
            else:
                self.incorporated_images[filename] = filename.replace("_", " ")

        for filename in self.incorporated_images.keys():
            if not os.path.exists(os.path.join(self.env_dict["directory"], filename)):
                desc = self.incorporated_images[filename]
                if desc.endswith(".png"):
                    desc = desc.replace(".png", "")
                print("{}: {}".format(filename, desc))
                response = openai.Image.create(prompt=desc, n=1, size="256x256")
                image_url = response["data"][0]["url"]
                download(image_url, filename)

    def get_proposed_images_from_message(self, messages):
        """
        Extracts proposed images from messages and downloads them.

        Args:
            messages (str): The messages containing proposed images.

        Returns:
            dict: A dictionary of the proposed images with filenames as keys and descriptions as values.
        """
        def download(img_url, file_name):
            r = requests.get(img_url)
            filepath = os.path.join(self.env_dict["directory"], file_name)
            if os.path.exists(filepath):
                os.remove(filepath)
            with open(filepath, "wb") as f:
                f.write(r.content)
                print("{} Downloaded".format(filepath))

        regex = r"(\w+.png):(.*?)\n"
        matches = re.finditer(regex, messages, re.DOTALL)
        images = {}
        for match in matches:
            filename = match.group(1).strip()
            desc = match.group(2).strip()
            images[filename] = desc

        if len(images.keys()) == 0:
            regex = r"(\w+.png)"
            matches = re.finditer(regex, messages, re.DOTALL)
            images = {}
            for match in matches:
                filename = match.group(1).strip()
                desc = " ".join(filename.replace(".png", "").split("_"))
                images[filename] = desc
                print("{}: {}".format(filename, images[filename]))

        for filename in images.keys():
            if not os.path.exists(os.path.join(self.env_dict["directory"], filename)):
                desc = images[filename]
                if desc.endswith(".png"):
                    desc = desc.replace(".png", "")
                print("{}: {}".format(filename, desc))
                response = openai.Image.create(prompt=desc, n=1, size="256x256")
                image_url = response["data"][0]["url"]
                download(image_url, filename)

        return images
