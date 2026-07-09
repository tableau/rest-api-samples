// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest;

import java.io.File;
import java.util.List;
import java.util.Map;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.tableausoftware.documentation.api.rest.bindings.GranteeCapabilitiesType;
import com.tableausoftware.documentation.api.rest.bindings.GroupType;
import com.tableausoftware.documentation.api.rest.bindings.ProjectListType;
import com.tableausoftware.documentation.api.rest.bindings.ProjectType;
import com.tableausoftware.documentation.api.rest.bindings.TableauCredentialsType;
import com.tableausoftware.documentation.api.rest.bindings.WorkbookListType;
import com.tableausoftware.documentation.api.rest.bindings.WorkbookType;
import com.tableausoftware.documentation.api.rest.util.RestApiUtils;

/**
 * Demonstrates Tableau REST API calls:
 * 1. Sign in
 * 2. Query projects, find the Default project
 * 3. Publish a workbook
 * 4. Create a group
 * 5. Add permissions on the workbook for the group
 * 6. Query workbooks for the current user
 * 7. Sign out
 */
public class Demo {

    private static final Logger logger = LogManager.getLogger(Demo.class);
    private static final RestApiUtils restApiUtils = RestApiUtils.getInstance();

    public static void main(String[] args) {
        String tokenName = RestApiUtils.getProperty("pat.token.name");
        String tokenSecret = RestApiUtils.getProperty("pat.token.secret");
        String contentUrl = RestApiUtils.getProperty("site.default.contentUrl");

        TableauCredentialsType credential = restApiUtils.invokeSignInWithPAT(tokenName, tokenSecret, contentUrl);
        String currentSiteId = credential.getSite().getId();
        String currentUserId = credential.getUser().getId();

        logger.info("Site ID: {}", currentSiteId);

        ProjectListType projects = restApiUtils.invokeQueryProjects(credential, currentSiteId);
        if (projects == null) {
            logger.error("Failed to query projects");
            restApiUtils.invokeSignOut(credential);
            return;
        }

        String targetProjectName = RestApiUtils.getProperty("project.name", "Default");
        ProjectType defaultProject = null;
        for (ProjectType project : projects.getProject()) {
            if (targetProjectName.equalsIgnoreCase(project.getName())) {
                defaultProject = project;
                logger.info("Project '{}' found: {}", project.getName(), project.getId());
                break;
            }
        }

        if (defaultProject == null) {
            logger.warn("No project named '{}' found. First 5 projects on site:", targetProjectName);
            projects.getProject().stream().limit(5).forEach(p ->
                    logger.warn("  '{}' ({})", p.getName(), p.getId()));
            logger.error("Failed to find project '{}'", targetProjectName);
            restApiUtils.invokeSignOut(credential);
            return;
        }

        String workbookName = RestApiUtils.getProperty("workbook.sample.name");
        String workbookPath = RestApiUtils.getProperty("workbook.sample.path");
        File workbookFile = new File(workbookPath);
        boolean chunkedPublish = Boolean.parseBoolean(RestApiUtils.getProperty("workbook.publish.chunked"));

        WorkbookType publishedWorkbook = restApiUtils.invokePublishWorkbook(credential, currentSiteId,
                defaultProject.getId(), workbookName, workbookFile, chunkedPublish);

        if (publishedWorkbook == null) {
            logger.error("Failed to publish workbook");
            restApiUtils.invokeSignOut(credential);
            return;
        }

        GroupType group = restApiUtils.invokeCreateGroup(credential, currentSiteId, "TableauExample");
        if (group == null) {
            logger.error("Failed to create group");
            restApiUtils.invokeSignOut(credential);
            return;
        }

        GranteeCapabilitiesType groupCapabilities = restApiUtils.createGroupGranteeCapability(
                group, Map.of("Read", "Allow", "ChangePermissions", "Deny"));

        restApiUtils.invokeAddPermissionsToWorkbook(credential, currentSiteId,
                publishedWorkbook.getId(), List.of(groupCapabilities));

        WorkbookListType userWorkbooks =
                restApiUtils.invokeQueryWorkbooks(credential, currentSiteId, currentUserId);
        if (userWorkbooks != null) {
            for (WorkbookType workbook : userWorkbooks.getWorkbook()) {
                if (workbook.getId().equals(publishedWorkbook.getId())) {
                    logger.debug("Published workbook found: {}", workbook.getId());
                    if (workbook.getOwner().getId().equals(currentUserId)) {
                        logger.debug("Published workbook was published by current user");
                    }
                }
            }
        }

        restApiUtils.invokeSignOut(credential);
    }
}
