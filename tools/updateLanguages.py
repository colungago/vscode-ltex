#!/usr/bin/python3

# Copyright (C) 2020 Julian Valentin, LTeX Development Community
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import glob
import json
import os
import re
import shlex
import subprocess
import sys

sys.path.append(os.path.dirname(__file__))
import common



toolsDirPath = os.path.join(common.repoDirPath, "tools")



def removeKeyIfPresent(d, key):
  if key in d: del d[key]



def run(cmd, **kwargs):
  print("Running {}...".format(" ".join(shlex.quote(x) for x in cmd)))
  return subprocess.run(cmd, stdout=subprocess.PIPE, cwd=toolsDirPath)

def fetchLanguages(toolsDirPath, ltexLsPath):
  classPath = os.pathsep.join([toolsDirPath, os.path.join(ltexLsPath, "lib", "*")])
  run(["javac", "-cp", classPath, "LanguageToolLanguageLister.java"])
  process = run(["java", "-cp", classPath, "LanguageToolLanguageLister"])
  stdout = process.stdout.decode()
  languages = sorted([dict(zip(("languageShortCode", "languageName"), line.split(";")))
      for line in stdout.splitlines()], key=lambda x: x["languageShortCode"])
  ltLanguageShortCodes = [x["languageShortCode"] for x in languages]
  ltLanguageNames = [x["languageName"] for x in languages]
  return ltLanguageShortCodes, ltLanguageNames



def updatePackageJson(ltLanguageShortCodes):
  packageJsonPath = os.path.join(common.repoDirPath, "package.json")
  with open(packageJsonPath, "r") as f: packageJson = json.load(f)
  settings = packageJson["contributes"]["configuration"]["properties"]

  settings["ltex.language"]["enum"] = ltLanguageShortCodes
  settings["ltex.language"]["enumDescriptions"] = [
      "%ltex.i18n.configuration.ltex.language.{}.enumDescription%".format(x)
      for x in ltLanguageShortCodes]

  removeKeyIfPresent(settings["ltex.dictionary"], "propertyNames")
  settings["ltex.dictionary"]["properties"] = {
        languageShortCode: {
          "type" : "array",
          "items" : {
            "type" : "string",
          },
          "markdownDescription" : "%ltex.i18n.configuration.ltex.dictionary."
            "{}.markdownDescription%".format(languageShortCode),
          "description" : "%ltex.i18n.configuration.ltex.dictionary."
            "{}.description%".format(languageShortCode),
        }
        for languageShortCode in ltLanguageShortCodes
      }

  removeKeyIfPresent(settings["ltex.disabledRules"], "propertyNames")
  settings["ltex.disabledRules"]["properties"] = {
        languageShortCode: {
          "type" : "array",
          "items" : {
            "type" : "string",
          },
          "markdownDescription" : "%ltex.i18n.configuration.ltex.disabledRules."
            "{}.markdownDescription%".format(languageShortCode),
          "description" : "%ltex.i18n.configuration.ltex.disabledRules."
            "{}.description%".format(languageShortCode),
        }
        for languageShortCode in ltLanguageShortCodes
      }

  removeKeyIfPresent(settings["ltex.enabledRules"], "propertyNames")
  settings["ltex.enabledRules"]["properties"] = {
        languageShortCode: {
          "type" : "array",
          "items" : {
            "type" : "string",
          },
          "markdownDescription" : "%ltex.i18n.configuration.ltex.enabledRules."
            "{}.markdownDescription%".format(languageShortCode),
          "description" : "%ltex.i18n.configuration.ltex.enabledRules."
            "{}.description%".format(languageShortCode),
        }
        for languageShortCode in ltLanguageShortCodes
      }

  removeKeyIfPresent(settings["ltex.hiddenFalsePositives"], "propertyNames")
  settings["ltex.hiddenFalsePositives"]["properties"] = {
        languageShortCode: {
          "type" : "array",
          "items" : {
            "type" : "string",
          },
          "markdownDescription" : "%ltex.i18n.configuration.ltex.hiddenFalsePositives."
            "{}.markdownDescription%".format(languageShortCode),
          "description" : "%ltex.i18n.configuration.ltex.hiddenFalsePositives."
            "{}.description%".format(languageShortCode),
        }
        for languageShortCode in ltLanguageShortCodes
      }

  with open(packageJsonPath, "w") as f:
    json.dump(packageJson, f, indent=2, ensure_ascii=False)
    f.write("\n")

def updatePackageNlsJson(ltLanguageShortCodes, ltLanguageNames, uiLanguage):
  packageNlsJsonPath = (os.path.join(common.repoDirPath, "package.nls.json") if uiLanguage == "en" else
      os.path.join(common.repoDirPath, "package.nls.{}.json".format(uiLanguage)))
  with open(packageNlsJsonPath, "r") as f: oldPackageNlsJson = json.load(f)

  newPackageNlsJson = {}

  for key, value in oldPackageNlsJson.items():
    if key == "ltex.i18n.configuration.ltex.language.description":
      newPackageNlsJson[key] = value

      for ltLanguageShortCode, ltLanguageName in zip(ltLanguageShortCodes, ltLanguageNames):
        prefix = f"ltex.i18n.configuration.ltex.language.{ltLanguageShortCode}"
        newPackageNlsJson[f"{prefix}.enumDescription"] = ltLanguageName

    elif re.match(r"^ltex\.i18n\.configuration\.ltex\.language\..+\.", key) is not None:
      continue

    elif key == "ltex.i18n.configuration.ltex.dictionary.description":
      newPackageNlsJson[key] = value

      for ltLanguageShortCode, ltLanguageName in zip(ltLanguageShortCodes, ltLanguageNames):
        prefix = f"ltex.i18n.configuration.ltex.dictionary.{ltLanguageShortCode}"

        if uiLanguage == "de":
          newPackageNlsJson[f"{prefix}.markdownDescription"] = (
              "Liste von zusätzlichen Wörtern der Sprache "
              f"`{ltLanguageShortCode}` ({ltLanguageName}), die nicht als Schreibfehler "
              "gewertet werden sollen.")
          newPackageNlsJson[f"{prefix}.description"] = (
              "Liste von zusätzlichen Wörtern der Sprache "
              f"'{ltLanguageShortCode}' ({ltLanguageName}), die nicht als Schreibfehler "
              "gewertet werden sollen.")
        else:
          newPackageNlsJson[f"{prefix}.markdownDescription"] = (
              f"List of additional `{ltLanguageShortCode}` ({ltLanguageName}) words that should "
              "not be counted as spelling errors.")
          newPackageNlsJson[f"{prefix}.description"] = (
              f"List of additional '{ltLanguageShortCode}' ({ltLanguageName}) words that should "
              "not be counted as spelling errors.")

    elif re.match(r"^ltex\.i18n\.configuration\.ltex\.dictionary\..+\.", key) is not None:
      continue

    elif key == "ltex.i18n.configuration.ltex.disabledRules.description":
      newPackageNlsJson[key] = value

      for ltLanguageShortCode, ltLanguageName in zip(ltLanguageShortCodes, ltLanguageNames):
        prefix = f"ltex.i18n.configuration.ltex.disabledRules.{ltLanguageShortCode}"

        if uiLanguage == "de":
          newPackageNlsJson[f"{prefix}.markdownDescription"] = (
              "Liste von zusätzlichen Regeln der Sprache "
              f"`{ltLanguageShortCode}` ({ltLanguageName}), die deaktiviert werden sollen "
              "(falls standardmäßig durch LanguageTool aktiviert).")
          newPackageNlsJson[f"{prefix}.description"] = (
              "Liste von zusätzlichen Regeln der Sprache "
              f"'{ltLanguageShortCode}' ({ltLanguageName}), die deaktiviert werden sollen "
              "(falls standardmäßig durch LanguageTool aktiviert).")
        else:
          newPackageNlsJson[f"{prefix}.markdownDescription"] = (
              f"List of additional `{ltLanguageShortCode}` ({ltLanguageName}) rules that should "
              "be disabled (if enabled by default by LanguageTool).")
          newPackageNlsJson[f"{prefix}.description"] = (
              f"List of additional '{ltLanguageShortCode}' ({ltLanguageName}) rules that should "
              "be disabled (if enabled by default by LanguageTool).")

    elif re.match(r"^ltex\.i18n\.configuration\.ltex\.disabledRules\..+\.", key) is not None:
      continue

    elif key == "ltex.i18n.configuration.ltex.hiddenFalsePositives.description":
      newPackageNlsJson[key] = value

      for ltLanguageShortCode, ltLanguageName in zip(ltLanguageShortCodes, ltLanguageNames):
        prefix = f"ltex.i18n.configuration.ltex.hiddenFalsePositives.{ltLanguageShortCode}"

        if uiLanguage == "de":
          newPackageNlsJson[f"{prefix}.markdownDescription"] = (
              "Liste von falschen Fehlern der Sprache "
              f"`{ltLanguageShortCode}` ({ltLanguageName}), die verborgen werden sollen .")
          newPackageNlsJson[f"{prefix}.description"] = (
              "Liste von falschen Fehlern der Sprache "
              f"'{ltLanguageShortCode}' ({ltLanguageName}), die verborgen werden sollen.")
        else:
          newPackageNlsJson[f"{prefix}.markdownDescription"] = (
              f"List of `{ltLanguageShortCode}` ({ltLanguageName}) false-positive diagnostics to hide.")
          newPackageNlsJson[f"{prefix}.description"] = (
              f"List of '{ltLanguageShortCode}' ({ltLanguageName}) false-positive diagnostics to hide.")

    elif re.match(r"^ltex\.i18n\.configuration\.ltex\.hiddenFalsePositives\..+\.", key) is not None:
      continue

    else:
      newPackageNlsJson[key] = value

  with open(packageNlsJsonPath, "w") as f:
    json.dump(newPackageNlsJson, f, indent=2, ensure_ascii=False)
    f.write("\n")



def main():
  parser = argparse.ArgumentParser(description="Fetch all supported language codes from "
      "LanguageTool and updates the language-specific parts of package.json accordingly")
  parser.add_argument("--ltex-ls-path", default="../ltex-ls/ltexls-core/target/appassembler",
      help="Path to ltex-ls relative from the root directory of LTeX, supports wildcards")
  args = parser.parse_args()

  ltexLsPaths = glob.glob(os.path.join(common.repoDirPath, args.ltex_ls_path))
  assert len(ltexLsPaths) > 0, "ltex-ls not found"
  assert len(ltexLsPaths) < 2, "multiple ltex-ls found via wildcard"
  ltexLsPath = ltexLsPaths[0]
  print("Using ltex-ls from {}".format(ltexLsPath))

  print("Fetching languages from LanguageTool...")
  ltLanguageShortCodes, ltLanguageNames = fetchLanguages(toolsDirPath, ltexLsPath)
  assert len(ltLanguageShortCodes) > 0, "No languages found."
  print("LanguageTool Languages: {}".format(", ".join(ltLanguageShortCodes)))

  print("Updating package.json...")
  updatePackageJson(ltLanguageShortCodes)

  print("Updating package.nls.json...")
  updatePackageNlsJson(ltLanguageShortCodes, ltLanguageNames, "en")

  for fileName in sorted(os.listdir(os.path.join(common.repoDirPath))):
    match = re.match(r"^package\.nls\.([A-Za-z0-9\-_]+)\.json$", fileName)
    if match is None: continue
    uiLanguage = match.group(1)
    print("Updating package.nls.{}.json...".format(uiLanguage))
    updatePackageNlsJson(ltLanguageShortCodes, ltLanguageNames, uiLanguage)



if __name__ == "__main__":
  main()
