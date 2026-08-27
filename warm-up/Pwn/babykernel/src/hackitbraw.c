#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/slab.h>
#include <linux/uaccess.h>

#define DEVICE_NAME "hackitbraw"
#define HIB_ALLOC _IO('h', 0x10)
#define HIB_FREE  _IO('h', 0x11)
#define HIB_WRITE _IOW('h', 0x12, struct hib_req)
#define HIB_CALL  _IO('h', 0x13)

struct hib_req {
    unsigned long len;
    unsigned long buf;
};

struct hackitbraw_obj {
    char note[0x40];
    void (*braw)(void);
};

static DEFINE_MUTEX(hib_lock);
static struct hackitbraw_obj *g_obj;

static void hib_default_braw(void)
{
    pr_info("hackitbraw: boring braw() called\n");
}

static long hib_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
    struct hib_req req;
    long ret = 0;

    mutex_lock(&hib_lock);

    switch (cmd) {
    case HIB_ALLOC:
        if (g_obj) {
            ret = -EBUSY;
            break;
        }
        g_obj = kzalloc(sizeof(*g_obj), GFP_KERNEL);
        if (!g_obj) {
            ret = -ENOMEM;
            break;
        }
        g_obj->braw = hib_default_braw;
        pr_info("hackitbraw: object allocated at %px\n", g_obj);
        break;

    case HIB_FREE:
        kfree(g_obj);
        g_obj = NULL;
        pr_info("hackitbraw: object freed\n");
        break;

    case HIB_WRITE:
        if (!g_obj) {
            ret = -EINVAL;
            break;
        }
        if (copy_from_user(&req, (void __user *)arg, sizeof(req))) {
            ret = -EFAULT;
            break;
        }

        if (copy_from_user(g_obj->note, (void __user *)req.buf, req.len)) {
            ret = -EFAULT;
            break;
        }
        pr_info("hackitbraw: wrote %lu bytes\n", req.len);
        break;

    case HIB_CALL:
        if (!g_obj || !g_obj->braw) {
            ret = -EINVAL;
            break;
        }
        pr_info("hackitbraw: calling braw=%px\n", g_obj->braw);
        g_obj->braw();
        break;

    default:
        ret = -ENOTTY;
        break;
    }

    mutex_unlock(&hib_lock);
    return ret;
}

static const struct file_operations hib_fops = {
    .owner = THIS_MODULE,
    .unlocked_ioctl = hib_ioctl,
#ifdef CONFIG_COMPAT
    .compat_ioctl = hib_ioctl,
#endif
};

static struct miscdevice hib_misc = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = DEVICE_NAME,
    .fops = &hib_fops,
    .mode = 0666,
};

static int __init hib_init(void)
{
    pr_info("hackitbraw: loaded; intentional CTF bug enabled\n");
    return misc_register(&hib_misc);
}

static void __exit hib_exit(void)
{
    misc_deregister(&hib_misc);
    kfree(g_obj);
    g_obj = NULL;
    pr_info("hackitbraw: unloaded\n");
}

module_init(hib_init);
module_exit(hib_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("HIBCHB26");
MODULE_DESCRIPTION("babykernel CTF module: hackitbraw ret2usr primitive");
