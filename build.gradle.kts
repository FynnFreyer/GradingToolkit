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
                // extract data from its path (like "repos:account:exercise")
                val parts = subproject.path.split(":")
                val studentName = parts[2]
                val exerciseName = parts[3]

                val studentReportDir = file("${aggregateDir}/${studentName}")
                studentReportDir.mkdirs()


                val subBuildDir = file(subproject.layout.buildDirectory).absolutePath
                val testResults = "${subBuildDir}/test-results/test"

                // retrieve test results and copy to output dir
                copy {
                    from(testResults) {
                        include("*.xml")
                    }
                    into(studentReportDir)
                    eachFile {
                        name = "${exerciseName}_${name}"
                    }
                }
            }
        }
    }
}
