#!/usr/bin/env groovy

import jenkins.branch.*
import jenkins.model.Jenkins

import com.dettonville.pipeline.utils.logging.LogLevel
import com.dettonville.pipeline.utils.logging.Logger

import com.dettonville.pipeline.utils.JsonUtils

Logger log = new Logger(this)

Map config = [:]

List testTags = [
    "update_inventory",
    "update_groups",
    "update_hosts",
    "all"
]

config.testCaseIdDefault = "group01"
config.testTagsParam = testTags
config.ansiblePlaybookDir = "./collections/ansible_collections/dettonville/git_inventory/tests/integration/targets"
// config.ansibleInventory = "${config.ansiblePlaybookDir}/_test_inventory/"

// log.info("config=${JsonUtils.printToJsonString(config)}")
log.info("config=${config}")

runAnsibleCollectionTest(config)
