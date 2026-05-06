/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onMounted, useRef } from "@odoo/owl";

// Masked Field Component for Odoo Sign
class SignMaskedField extends Component {
    setup() {
        this.state = useState({ value: this.props.value || "", showValue: false });
        this.inputRef = useRef("input");
    }

    onInput(ev) {
        const newValue = ev.target.value;
        this.state.value = newValue;
        if (this.props.update) {
            this.props.update(newValue);
        }
    }

    toggleVisibility() {
        this.state.showValue = !this.state.showValue;
    }
}

SignMaskedField.template = "cgc_sign_masked_field.SignMaskedField";
SignMaskedField.props = {
    ...standardFieldProps,
    value: { type: String, optional: true },
    update: { type: Function, optional: true },
};

// Register the masked field in the sign field registry
const signFieldRegistry = registry.category("sign_fields");

signFieldRegistry.add("masked", {
    component: SignMaskedField,
    supportedTypes: ["text"],
    extractValue: (element) => element.textContent || "",
    setValue: (element, value) => {
        const input = element.querySelector("input[type='password'], input[type='text']");
        if (input) {
            input.value = value;
        }
    },
});
