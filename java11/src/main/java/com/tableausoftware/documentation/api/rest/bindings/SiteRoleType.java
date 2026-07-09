// Copyright (c) 2016 Tableau. Licensed under the MIT License.
// SPDX-License-Identifier: MIT
package com.tableausoftware.documentation.api.rest.bindings;

import jakarta.xml.bind.annotation.XmlEnum;
import jakarta.xml.bind.annotation.XmlEnumValue;
import jakarta.xml.bind.annotation.XmlType;

@XmlType(name = "siteRoleType")
@XmlEnum
public enum SiteRoleType {

    @XmlEnumValue("Creator") CREATOR("Creator"),
    @XmlEnumValue("Explorer") EXPLORER("Explorer"),
    @XmlEnumValue("ExplorerCanPublish") EXPLORER_CAN_PUBLISH("ExplorerCanPublish"),
    @XmlEnumValue("Guest") GUEST("Guest"),
    @XmlEnumValue("ServerAdministrator") SERVER_ADMINISTRATOR("ServerAdministrator"),
    @XmlEnumValue("SiteAdministratorCreator") SITE_ADMINISTRATOR_CREATOR("SiteAdministratorCreator"),
    @XmlEnumValue("SiteAdministratorExplorer") SITE_ADMINISTRATOR_EXPLORER("SiteAdministratorExplorer"),
    @XmlEnumValue("SupportUser") SUPPORT_USER("SupportUser"),
    @XmlEnumValue("Unlicensed") UNLICENSED("Unlicensed"),
    @XmlEnumValue("Viewer") VIEWER("Viewer");

    private final String value;

    SiteRoleType(String v) { value = v; }

    public String value() { return value; }

    public static SiteRoleType fromValue(String v) {
        for (SiteRoleType c : SiteRoleType.values()) {
            if (c.value.equals(v)) return c;
        }
        throw new IllegalArgumentException(v);
    }
}
