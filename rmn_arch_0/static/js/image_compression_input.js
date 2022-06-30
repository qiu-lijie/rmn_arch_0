import Compressor from './compressor.esm.js';
import { get_or_create_error_p, set_error_p } from './form_validation.js';

/**
 * CompressorNode that holdes it own index to deal with callback hell
 * @param {number} index position of this CompressorNode
 * @param {function} callback function to call when successed or failed
 * @param {file} file image file to compress
 */
const CompressorNode = class {
    constructor(index, callback, file) {
        this.index = index;
        this.callback = callback;
        this.compressor = new Compressor(file, {
            checkOrientation: false,
            maxWidth: 800,
            maxHeight: 800,
            quality: 0.8,
            convertSize: 1000000,
            success: (res) => {
                if (!(res instanceof File)) {
                    res = new File([res], `image${this.index}.jpg`);
                }
                this.data = res;
                this.callback();
            },
            error: (err) => {
                // NOTE error in called when aborting
                this.callback();
            },
        });
    }
};

/**
 * A image input preview the selected image, compress it, then reattach it to the
 * original input element
 * Note this input
 *  - coverts png to jpg if size is too big,
 *  - strips the EXIF info in the process of compression
 *  - keeps gif untouched
 * @param {string} input_id     id of input element
 * @param {string} output_id    id of preview elements, in the form of `${output_id}${i}`
 * @param {number} size         number of images to preview and compress, at least 1
 */
export const ImageCompressionInput = class {
    constructor(input_id, output_id, size) {
        this.size = size;
        this.complete_count = 0;
        this.data = [];
        this.compressor_nodes = [];
        this.input_elem = document.getElementById(input_id);
        this.output_elems = [];
        for (let i = 0; i < size; i++) {
            this.output_elems.push(document.getElementById(`${output_id}${i}`));
        }
        this.default_src = this.output_elems[0].src;
        this.error_elem = get_or_create_error_p(input_id);
        this.submit_elem = document.querySelector('button[type="submit"]');

        this.input_elem.addEventListener('change', (event) => this.input_handler(event), false);
    }

    input_handler(event) {
        const files = event.target.files;
        // check files length
        if (files.length > this.size) {
            set_error_p(
                this.error_elem,
                true,
                `You can only upload ${this.size} images
                <br>you have selected ${files.length}`
            );
            return;
        } else {
            set_error_p(this.error_elem, false);
        }

        // create new CompressNode (thus Compressor) for each image
        this.submit_elem.disabled = true;
        this.compressor_nodes.forEach((cn) => {
            cn.compressor.abort();
        });
        this.data = Array.from(files);
        this.complete_count = 0;
        this.compressor_nodes = [];
        let i = 0;
        for (; i < files.length; i++) {
            this.output_elems[i].src = URL.createObjectURL(files[i]);
            if (files[i].type === 'image/gif') {
                this.complete();
                continue;
            }
            this.compressor_nodes.push(
                new CompressorNode(
                    i,
                    () => {
                        this.complete();
                    },
                    files[i]
                )
            );
        }

        // reset preview images if necessary
        for (; i < this.size; i++) {
            this.output_elems[i].src = this.default_src;
            this.complete();
        }
    }

    complete() {
        this.complete_count++;
        if (this.complete_count == this.size) {
            let lst = new DataTransfer();
            for (let cn of this.compressor_nodes) {
                if (cn.data) {
                    this.data[cn.index] = cn.data;
                }
            }
            this.data.forEach((data) => {
                lst.items.add(data);
            });
            this.input_elem.files = lst.files;
            this.submit_elem.disabled = false;
        }
    }
};
