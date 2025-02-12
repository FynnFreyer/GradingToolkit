subprojects {
    // continue despite failed tests
    tasks.withType<Test>() {
        ignoreFailures = true
    }

    // continue despite compile errors
    tasks.withType<JavaCompile>() {
        options.isFailOnError = false
    }
}

tasks.register("aggregate") {
    val aggregateDir = file("build/reports/aggregate")
    // declare and create output dir
    outputs.dir(aggregateDir)
    aggregateDir.mkdirs()

    doLast {
        // for each subproject
        subprojects.forEach { subproject ->
            // for each test task
            subproject.tasks.withType<Test>() {
                // extract data from its path (like "repos:exercise:account")
                val parts = subproject.path.split(":")
                val assignmentSlug = parts[2]
                val studentGithubName = parts[3]

                val studentReportDir = file("${aggregateDir}/${studentGithubName}")
                studentReportDir.mkdirs()

                val subBuildDir = file(subproject.layout.buildDirectory)
                val testResults = "${subBuildDir.absolutePath}/test-results/test"

                // retrieve test results and copy to output dir
                copy {
                    from(testResults) {
                        include("*.xml")
                    }
                    into(studentReportDir)
                    eachFile {
                        name = "${assignmentSlug}_${name}"
                    }
                }
            }
        }
    }
}
