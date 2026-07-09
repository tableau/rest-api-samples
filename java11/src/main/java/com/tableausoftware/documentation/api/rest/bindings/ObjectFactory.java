// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlRegistry;

@XmlRegistry
public class ObjectFactory {

    public ObjectFactory() {}

    public GranteeCapabilitiesType createGranteeCapabilitiesType() { return new GranteeCapabilitiesType(); }
    public SiteType createSiteType() { return new SiteType(); }
    public TsResponse createTsResponse() { return new TsResponse(); }
    public TableauCredentialsType createTableauCredentialsType() { return new TableauCredentialsType(); }
    public GroupType createGroupType() { return new GroupType(); }
    public PermissionsType createPermissionsType() { return new PermissionsType(); }
    public ProjectType createProjectType() { return new ProjectType(); }
    public WorkbookType createWorkbookType() { return new WorkbookType(); }
    public TsRequest createTsRequest() { return new TsRequest(); }
    public CapabilityType createCapabilityType() { return new CapabilityType(); }
    public GranteeCapabilitiesType.Capabilities createGranteeCapabilitiesTypeCapabilities() {
        return new GranteeCapabilitiesType.Capabilities();
    }
}
